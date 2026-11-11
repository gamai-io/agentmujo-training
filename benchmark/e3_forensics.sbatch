#!/bin/bash
# Cross-process forensics: 4 arms x 3 repeats, token logprobs captured.
# Arms restart the server, so arm-to-arm is also cross-process.
#   base       : default kernels
#   bi         : VLLM_BATCH_INVARIANT=1
#   triton     : --attention-backend TRITON_ATTN
#   bi_triton  : both
#SBATCH --job-name=amj_forensic
#SBATCH --account=project_465003647
#SBATCH --partition=dev-g
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=56
#SBATCH --gres=gpu:mi250:4
#SBATCH --time=02:00:00
#SBATCH --output=/project/project_465003647/gama/out/forensic_%j.out
set -uo pipefail
BASE=/project/project_465003647/gama
KIT=$BASE/bench_v2
OUT=$BASE/out
MODEL=${MODEL:-/scratch/project_465003647/models/qwen25-7b}
ITEMS=${ITEMS:-$KIT/items_v2.jsonl}
N=${N:-100}
CONC=${CONC:-8}
MAXTOK=${MAXTOK:-64}
TP=${TP:-1}
PORT=${PORT:-8000}
ARMS=${ARMS:-"base bi triton bi_triton"}
mkdir -p "$OUT"
module purge >/dev/null 2>&1 || true
module load Local-LAIF lumi-aif-singularity-bindings
SIF=/appl/local/laifs/containers/lumi-multitorch-latest.sif

echo "HOST=$(hostname) DATE=$(date -u) ARMS=$ARMS N=$N CONC=$CONC TP=$TP"

serve () {
  local tag=$1 extra=${2:-}
  env BI=0 ATTN=0
  case "$tag" in
    bi) BI=1 ;;
    triton) ATTN=1 ;;
    bi_triton) BI=1; ATTN=1 ;;
  esac
  local args=""
  if [ "$BI" = 1 ]; then
    export VLLM_BATCH_INVARIANT=1
    export SINGULARITYENV_VLLM_BATCH_INVARIANT=1
  fi
  if [ "$ATTN" = 1 ]; then
    args="--attention-backend TRITON_ATTN"
  fi
  srun -n1 --gres=gpu:mi250:"$TP" --cpus-per-task=32 singularity exec \
    -B /scratch:/scratch -B /project:/project -B /appl/local/laifs:/appl/local/laifs "$SIF" \
    python -m vllm.entrypoints.openai.api_server \
      --model "$MODEL" --served-model-name qwen --host 127.0.0.1 --port "$PORT" \
      --tensor-parallel-size "$TP" --max-model-len 8192 --max-num-seqs 256 \
      --gpu-memory-utilization 0.90 --trust-remote-code $args \
      > "$OUT/vllm_fx_${tag}_$SLURM_JOB_ID.log" 2>&1 &
  SPID=$!
  for i in $(seq 1 420); do
    curl -sf "http://127.0.0.1:$PORT/v1/models" >/dev/null && return 0
    sleep 2
  done
  return 1
}

for arm in $ARMS; do
  echo "=== ARM $arm $(date -u)"
  if ! serve "$arm"; then
    echo "VLLM_FAIL $arm"; tail -12 "$OUT/vllm_fx_${arm}_$SLURM_JOB_ID.log"
    kill "$SPID" 2>/dev/null; wait "$SPID" 2>/dev/null; sleep 3
    continue
  fi
  echo "VLLM_READY $arm $(date -u)"
  for R in 1 2 3; do
    srun --overlap --jobid="$SLURM_JOB_ID" -n1 --cpus-per-task=16 singularity exec \
      -B /scratch:/scratch -B /project:/project "$SIF" \
      python3 "$KIT/forensics_client.py" --url "http://127.0.0.1:$PORT" --model qwen \
        --items "$ITEMS" --n "$N" --conc "$CONC" --max-tokens "$MAXTOK" \
        --out "$OUT/fx_${arm}_r${R}_$SLURM_JOB_ID.jsonl"
    echo "REP_DONE $arm r$R rc=$?"
  done
  kill "$SPID" 2>/dev/null; wait "$SPID" 2>/dev/null; sleep 5
done

cat > "$OUT/fx_cmp_$SLURM_JOB_ID.py" <<'PY'
import glob, json, os, statistics, sys
out, job = sys.argv[1], sys.argv[2]
arms = sys.argv[3].split(",")

def load(arm, r):
    p = os.path.join(out, f"fx_{arm}_r{r}_{job}.jsonl")
    if not os.path.exists(p):
        return None
    return {x["id"]: x for x in (json.loads(l) for l in open(p, encoding="utf-8") if l.strip())}

def first_div(a, b):
    ta, tb = a.get("tokens") or [], b.get("tokens") or []
    for i, (x, y) in enumerate(zip(ta, tb)):
        if x != y:
            return i
    return None if len(ta) == len(tb) else min(len(ta), len(tb))

res = {"job": job, "arms": {}}
for arm in arms:
    runs = {r: load(arm, r) for r in (1, 2, 3)}
    if not runs[1]:
        res["arms"][arm] = {"available": False}
        continue
    pairs = [(1, 2), (1, 3)]
    stats = {}
    for x, y in pairs:
        if not runs[y]:
            continue
        ids = [i for i in runs[x] if i in runs[y]]
        diffs = [i for i in ids if (runs[x][i].get("tokens") or []) != (runs[y][i].get("tokens") or [])]
        fd = [first_div(runs[x][i], runs[y][i]) for i in diffs]
        fd = [f for f in fd if f is not None]
        lpdelta = []
        for i in diffs[:50]:
            a = runs[x][i]; b = runs[y][i]; f = first_div(a, b)
            if f is not None and f < len(a.get("logprobs") or []) and f < len(b.get("logprobs") or []):
                lpdelta.append(abs(a["logprobs"][f] - b["logprobs"][f]))
        stats[f"r{x}_vs_r{y}"] = {
            "n": len(ids), "flips": len(diffs),
            "flip_rate": round(len(diffs) / len(ids), 4) if ids else 0.0,
            "first_div_median": int(statistics.median(fd)) if fd else None,
            "first_div_max": max(fd) if fd else None,
            "logprob_delta_mean": round(statistics.mean(lpdelta), 4) if lpdelta else None,
        }
    res["arms"][arm] = {"available": True, "pairs": stats}

json.dump(res, open(os.path.join(out, f"e2_forensics_{job}.json"), "w"), indent=2)
print(json.dumps(res, indent=2))
PY
srun --overlap --jobid="$SLURM_JOB_ID" -n1 --cpus-per-task=4 singularity exec \
  -B /scratch:/scratch -B /project:/project "$SIF" \
  python3 "$OUT/fx_cmp_$SLURM_JOB_ID.py" "$OUT" "$SLURM_JOB_ID" "$(echo $ARMS | tr ' ' ',')"
echo "FORENSIC_DONE $(date -u)"
