#!/bin/bash
# VLLM_BATCH_INVARIANT=1 on MI250X (gfx90a): does it remove the residual flips?
# Three passes: A and B in one server process (batch/order invariance),
# C after a server restart (cross-process reproducibility).
# Baseline (no flag, same workload): TP=4 660/700, TP=1 669/700 identical.
#SBATCH --job-name=amj_bi
#SBATCH --account=project_465003647
#SBATCH --partition=dev-g
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=56
#SBATCH --gres=gpu:mi250:4
#SBATCH --time=02:30:00
#SBATCH --output=/project/project_465003647/gama/out/bi_%j.out
set -uo pipefail
BASE=/project/project_465003647/gama
KIT=$BASE/bench_v2
OUT=$BASE/out
MODEL=${MODEL:-/scratch/project_465003647/models/qwen25-7b}
ITEMS=${ITEMS:-$KIT/items_v2.jsonl}
TP=${TP:-1}
PORT=${PORT:-8000}
MAXTOK=${MAXTOK:-256}
CONC=${CONC:-64}
MAXSEQS=${MAXSEQS:-256}
BI=${BI:-1}
OUTJSON=${OUTJSON:-$OUT/e2_batchinvariant_tp${TP}_$SLURM_JOB_ID.json}
mkdir -p "$OUT"
module purge >/dev/null 2>&1 || true
module load Local-LAIF lumi-aif-singularity-bindings
SIF=/appl/local/laifs/containers/lumi-multitorch-latest.sif

export VLLM_BATCH_INVARIANT="$BI"
export SINGULARITYENV_VLLM_BATCH_INVARIANT="$BI"
echo "HOST=$(hostname) DATE=$(date -u) TP=$TP BI=$BI CONC=$CONC MAXSEQS=$MAXSEQS"

serve () {
  srun -n1 --gres=gpu:mi250:"$TP" --cpus-per-task=32 singularity exec \
    -B /scratch:/scratch -B /project:/project -B /appl/local/laifs:/appl/local/laifs "$SIF" \
    python -m vllm.entrypoints.openai.api_server \
      --model "$MODEL" --served-model-name qwen --host 127.0.0.1 --port "$PORT" \
      --tensor-parallel-size "$TP" --max-model-len 8192 --max-num-seqs "$MAXSEQS" \
      --gpu-memory-utilization 0.90 --trust-remote-code \
      > "$OUT/vllm_bi_tp${TP}_${1}_$SLURM_JOB_ID.log" 2>&1 &
  SPID=$!
  for i in $(seq 1 420); do
    curl -sf "http://127.0.0.1:$PORT/v1/models" >/dev/null && return 0
    sleep 2
  done
  return 1
}

stop () { kill "$SPID" 2>/dev/null; wait "$SPID" 2>/dev/null; sleep 6; }

pass () {
  local name=$1
  srun --overlap --jobid="$SLURM_JOB_ID" -n1 --cpus-per-task=16 singularity exec \
    -B /scratch:/scratch -B /project:/project "$SIF" \
    python3 "$KIT/run_v2.py" --url "http://127.0.0.1:$PORT" --model qwen \
      --items "$ITEMS" --n 0 --conc "$CONC" --max-tokens "$MAXTOK" \
      --out "$OUT/bi_${name}_tp${TP}_$SLURM_JOB_ID.jsonl" \
      --summary "$OUT/bi_${name}_tp${TP}_$SLURM_JOB_ID.summary.json"
  echo "PASS_${name}_DONE rc=$?"
}

if ! serve first; then echo "VLLM_FAIL"; tail -25 "$OUT/vllm_bi_tp${TP}_first_$SLURM_JOB_ID.log"; exit 3; fi
echo "VLLM_READY_1 $(date -u)"
grep -i "batch.invarian" "$OUT/vllm_bi_tp${TP}_first_$SLURM_JOB_ID.log" | head -3 || true
pass a
pass b
stop
if ! serve second; then echo "VLLM_FAIL_2"; exit 3; fi
echo "VLLM_READY_2 $(date -u)"
pass c

cat > "$OUT/bi_compare_$SLURM_JOB_ID.py" <<'PY'
import hashlib, json, os, sys
out, job, tp = sys.argv[1], sys.argv[2], sys.argv[3]
dest = sys.argv[4] if len(sys.argv) > 4 else os.path.join(out, f"e2_batchinvariant_{job}.json")
def load(tag):
    p = os.path.join(out, f"bi_{tag}_tp{tp}_{job}.jsonl")
    return {r["id"]: r for r in (json.loads(l) for l in open(p, encoding="utf-8") if l.strip())}
runs = {t: load(t) for t in ("a", "b", "c")}
def cmp(x, y):
    ids = [i for i in runs[x] if i in runs[y]]
    same = sum(1 for i in ids if runs[x][i].get("text") == runs[y][i].get("text")
               and bool(runs[x][i].get("ok")) == bool(runs[y][i].get("ok")))
    return {"n": len(ids), "identical": same, "differing": len(ids) - same,
            "rate": round(same / len(ids), 4) if ids else 0.0}
def digest(t):
    h = hashlib.sha256()
    for i in sorted(runs[t]):
        h.update((runs[t][i].get("text") or "").encode()); h.update(b"\x00")
    return h.hexdigest()
res = {"job": job, "tp": int(tp), "batch_invariant": 1,
       "same_process": cmp("a", "b"), "cross_process": cmp("a", "c"),
       "sha_a": digest("a"), "sha_b": digest("b"), "sha_c": digest("c"),
       "verdict": "BIT_IDENTICAL" if cmp("a","b")["identical"] == cmp("a","b")["n"]
                  and cmp("a","c")["identical"] == cmp("a","c")["n"] else "NOT_BIT_IDENTICAL"}
json.dump(res, open(dest, "w"), indent=2)
print(json.dumps(res, indent=2))
PY
srun --overlap --jobid="$SLURM_JOB_ID" -n1 --cpus-per-task=4 singularity exec \
  -B /scratch:/scratch -B /project:/project "$SIF" \
  python3 "$OUT/bi_compare_$SLURM_JOB_ID.py" "$OUT" "$SLURM_JOB_ID" "$TP" "$OUTJSON"
echo "BI_DONE $(date -u)"
