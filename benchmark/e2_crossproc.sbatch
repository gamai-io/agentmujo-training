#!/bin/bash
# Cross-process reproducibility: N independent server starts, one pass each.
# Turns the single A-vs-C comparison into a distribution (pairwise identity matrix).
# Default: BI=1 (the mode that is deterministic within a process).
#SBATCH --job-name=amj_xproc
#SBATCH --account=project_465003647
#SBATCH --partition=dev-g
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=56
#SBATCH --gres=gpu:mi250:4
#SBATCH --time=01:30:00
#SBATCH --output=/project/project_465003647/gama/out/xproc_%j.out
set -uo pipefail
BASE=/project/project_465003647/gama
KIT=$BASE/bench_v2
OUT=$BASE/out
MODEL=${MODEL:-/scratch/project_465003647/models/qwen25-7b}
ITEMS=${ITEMS:-$KIT/items_v2.jsonl}
REPEATS=${REPEATS:-5}
N=${N:-200}
CONC=${CONC:-64}
MAXTOK=${MAXTOK:-128}
TP=${TP:-1}
BI=${BI:-1}
PORT=${PORT:-8000}
mkdir -p "$OUT"
module purge >/dev/null 2>&1 || true
module load Local-LAIF lumi-aif-singularity-bindings
SIF=/appl/local/laifs/containers/lumi-multitorch-latest.sif
if [ "$BI" = 1 ]; then
  export VLLM_BATCH_INVARIANT=1
  export SINGULARITYENV_VLLM_BATCH_INVARIANT=1
fi
echo "HOST=$(hostname) DATE=$(date -u) REPEATS=$REPEATS N=$N TP=$TP BI=$BI"

for r in $(seq 1 "$REPEATS"); do
  echo "=== run $r $(date -u)"
  srun -n1 --gres=gpu:mi250:"$TP" --cpus-per-task=32 singularity exec \
    -B /scratch:/scratch -B /project:/project -B /appl/local/laifs:/appl/local/laifs "$SIF" \
    python -m vllm.entrypoints.openai.api_server \
      --model "$MODEL" --served-model-name qwen --host 127.0.0.1 --port "$PORT" \
      --tensor-parallel-size "$TP" --max-model-len 8192 --max-num-seqs 256 \
      --gpu-memory-utilization 0.90 --trust-remote-code \
      > "$OUT/vllm_xp_r${r}_$SLURM_JOB_ID.log" 2>&1 &
  SPID=$!
  ok=0
  for i in $(seq 1 420); do
    curl -sf "http://127.0.0.1:$PORT/v1/models" >/dev/null && { ok=1; break; }
    sleep 2
  done
  if [ "$ok" != 1 ]; then echo "VLLM_FAIL r=$r"; kill "$SPID" 2>/dev/null; continue; fi
  srun --overlap --jobid="$SLURM_JOB_ID" -n1 --cpus-per-task=16 singularity exec \
    -B /scratch:/scratch -B /project:/project "$SIF" \
    python3 "$KIT/run_v2.py" --url "http://127.0.0.1:$PORT" --model qwen \
      --items "$ITEMS" --n "$N" --conc "$CONC" --max-tokens "$MAXTOK" \
      --out "$OUT/xp_r${r}_$SLURM_JOB_ID.jsonl" \
      --summary "$OUT/xp_r${r}_$SLURM_JOB_ID.summary.json"
  echo "RUN_DONE r=$r rc=$?"
  kill "$SPID" 2>/dev/null; wait "$SPID" 2>/dev/null; sleep 5
done

cat > "$OUT/xp_cmp_$SLURM_JOB_ID.py" <<'PY'
import glob, itertools, json, os, sys
OUT, JOB, REPEATS = sys.argv[1], sys.argv[2], int(sys.argv[3])
runs = {}
for r in range(1, REPEATS + 1):
    p = os.path.join(OUT, f"xp_r{r}_{JOB}.jsonl")
    if os.path.exists(p):
        runs[r] = {x["id"]: x for x in (json.loads(l) for l in open(p, encoding="utf-8") if l.strip())}
keys = sorted(runs)
pairs = []
for a, b in itertools.combinations(keys, 2):
    ids = [i for i in runs[a] if i in runs[b]]
    same = sum(1 for i in ids if (runs[a][i].get("tokens") or runs[a][i].get("text")) ==
               (runs[b][i].get("tokens") or runs[b][i].get("text")))
    pairs.append({"a": a, "b": b, "n": len(ids), "identical": same,
                  "rate": round(same / len(ids), 4) if ids else 0.0})
rates = [p["rate"] for p in pairs]
res = {"job": JOB, "runs": len(keys), "repeat": REPEATS, "pairs": pairs,
       "mean_identity": round(sum(rates) / len(rates), 4) if rates else None,
       "min_identity": min(rates) if rates else None,
       "max_identity": max(rates) if rates else None}
json.dump(res, open(os.path.join(OUT, f"e2_crossproc_{JOB}.json"), "w"), indent=2)
print(json.dumps(res, indent=2))
PY
srun --overlap --jobid="$SLURM_JOB_ID" -n1 --cpus-per-task=4 singularity exec \
  -B /scratch:/scratch -B /project:/project "$SIF" \
  python3 "$OUT/xp_cmp_$SLURM_JOB_ID.py" "$OUT" "$SLURM_JOB_ID" "$REPEATS"
echo "XPROC_DONE $(date -u)"
