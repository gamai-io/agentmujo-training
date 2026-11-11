#!/bin/bash
# E14 attribution error: 200 items x 3 models. Non-causal scenarios (system healed first)
# should be answered SYSTEM; causal ones AGENT. AER = share of non-causal answered AGENT.
#SBATCH --job-name=amj_e14
#SBATCH --account=project_465003647
#SBATCH --partition=dev-g
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=56
#SBATCH --gres=gpu:mi250:4
#SBATCH --time=01:00:00
#SBATCH --output=/project/project_465003647/gama/out/e14_%j.out
set -uo pipefail
BASE=/project/project_465003647/gama
KIT=$BASE/bench_v2
OUT=$BASE/out
MODELS_DIR=/scratch/project_465003647/models
ITEMS=${ITEMS:-$KIT/items_e14.jsonl}
N=${N:-200}
CONC=${CONC:-32}
TP=${TP:-4}
PORT=${PORT:-8000}
mkdir -p "$OUT"
module purge >/dev/null 2>&1 || true
module load Local-LAIF lumi-aif-singularity-bindings
SIF=/appl/local/laifs/containers/lumi-multitorch-latest.sif
echo "HOST=$(hostname) DATE=$(date -u) N=$N"
[ -f "$ITEMS" ] || { echo MISSING_ITEMS; exit 3; }

for spec in "qwen25-7b:qwen" "mistral-7b-instruct-v0.3:mistral" "phi35-mini-instruct:phi35"; do
  M="${spec%%:*}"; TAG="${spec##*:}"
  [ -d "$MODELS_DIR/$M" ] || { echo "MISSING_MODEL $M"; continue; }
  srun -n1 --gres=gpu:mi250:"$TP" --cpus-per-task=32 singularity exec \
    -B /scratch:/scratch -B /project:/project -B /appl/local/laifs:/appl/local/laifs "$SIF" \
    python -m vllm.entrypoints.openai.api_server \
      --model "$MODELS_DIR/$M" --served-model-name "$TAG" --host 127.0.0.1 --port "$PORT" \
      --tensor-parallel-size "$TP" --max-model-len 4096 --max-num-seqs 128 \
      --gpu-memory-utilization 0.90 --trust-remote-code \
      > "$OUT/vllm_e14_${TAG}_$SLURM_JOB_ID.log" 2>&1 &
  SPID=$!
  ok=0
  for i in $(seq 1 420); do curl -sf "http://127.0.0.1:$PORT/v1/models" >/dev/null && { ok=1; break; }; sleep 2; done
  if [ "$ok" != 1 ]; then echo "VLLM_FAIL $TAG"; kill "$SPID" 2>/dev/null; continue; fi
  echo "READY $TAG $(date -u)"
  srun --overlap --jobid="$SLURM_JOB_ID" -n1 --cpus-per-task=16 singularity exec \
    -B /scratch:/scratch -B /project:/project "$SIF" \
    python3 "$KIT/e14_client.py" --url "http://127.0.0.1:$PORT" --model "$TAG" \
      --items "$ITEMS" --n "$N" --conc "$CONC" --out "$OUT/v14_${TAG}_$SLURM_JOB_ID.jsonl"
  echo "RUN_DONE $TAG rc=$?"
  kill "$SPID" 2>/dev/null; wait "$SPID" 2>/dev/null; sleep 5
done

cat > "$OUT/e14_cmp_$SLURM_JOB_ID.py" <<'PY'
import glob, json, os, sys
OUT, JOB = sys.argv[1], sys.argv[2]
res = {"job": JOB, "models": {}}
for p in sorted(glob.glob(os.path.join(OUT, f"v14_*_{JOB}.jsonl"))):
    tag = os.path.basename(p).split("_")[1]
    rows = [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()]
    nc = [r for r in rows if r["kind"] == "noncausal"]
    ca = [r for r in rows if r["kind"] == "causal"]
    aer = sum(1 for r in nc if r["verdict"] == "AGENT")
    sysc = sum(1 for r in nc if r["verdict"] == "SYSTEM")
    acc = sum(1 for r in ca if r["verdict"] == "AGENT")
    res["models"][tag] = {
        "noncausal_n": len(nc), "attribution_errors": aer,
        "attribution_error_rate": round(aer / len(nc), 4) if nc else None,
        "correctly_system": sysc,
        "causal_n": len(ca), "correctly_agent": acc,
        "causal_accuracy": round(acc / len(ca), 4) if ca else None,
        "unparsed": sum(1 for r in rows if r["verdict"] == "UNPARSED"),
        "errors": sum(1 for r in rows if r["verdict"] == "ERR"),
    }
json.dump(res, open(os.path.join(OUT, f"e14_attribution_{JOB}.json"), "w"), indent=2)
print(json.dumps(res, indent=2))
PY
srun --overlap --jobid="$SLURM_JOB_ID" -n1 --cpus-per-task=4 singularity exec \
  -B /scratch:/scratch -B /project:/project "$SIF" \
  python3 "$OUT/e14_cmp_$SLURM_JOB_ID.py" "$OUT" "$SLURM_JOB_ID"
echo "E14_DONE $(date -u)"
