#!/bin/bash
# E12b: same as E12 self_ref, but the verifier prompt states a numeric tolerance.
# Purpose: test whether the 72% false-alarm rate was a format artefact or a model bias.
#SBATCH --job-name=amj_verifnum
#SBATCH --account=project_465003647
#SBATCH --partition=dev-g
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=56
#SBATCH --gres=gpu:mi250:4
#SBATCH --time=00:40:00
#SBATCH --output=/project/project_465003647/gama/out/e12b_%j.out
set -uo pipefail
BASE=/project/project_465003647/gama
KIT=$BASE/bench_v2
OUT=$BASE/out
ITEMS=$KIT/items_honesty_real.jsonl
ANSWERS=$OUT/v2hr_qwen_s42_23623454.jsonl
N=${N:-300}
CONC=${CONC:-32}
TP=${TP:-4}
PORT=${PORT:-8000}
MODEL_PATH=${MODEL_PATH:-/scratch/project_465003647/models/qwen25-7b}
MODEL_TAG=${MODEL_TAG:-qwen}
module purge >/dev/null 2>&1 || true
module load Local-LAIF lumi-aif-singularity-bindings
SIF=/appl/local/laifs/containers/lumi-multitorch-latest.sif
echo "HOST=$(hostname) DATE=$(date -u)"

srun -n1 --gres=gpu:mi250:"$TP" --cpus-per-task=32 singularity exec \
  -B /scratch:/scratch -B /project:/project -B /appl/local/laifs:/appl/local/laifs "$SIF" \
  python -m vllm.entrypoints.openai.api_server \
    --model "$MODEL_PATH" --served-model-name "$MODEL_TAG" \
    --host 127.0.0.1 --port "$PORT" --tensor-parallel-size "$TP" --max-model-len 8192 \
    --max-num-seqs 256 --gpu-memory-utilization 0.90 --trust-remote-code \
    > "$OUT/vllm_e12b_$SLURM_JOB_ID.log" 2>&1 &
SPID=$!
for i in $(seq 1 420); do curl -sf "http://127.0.0.1:$PORT/v1/models" >/dev/null && break; sleep 2; done
curl -sf "http://127.0.0.1:$PORT/v1/models" >/dev/null || { echo VLLM_FAIL; exit 4; }
echo "READY $(date -u)"

srun --overlap --jobid="$SLURM_JOB_ID" -n1 --cpus-per-task=16 singularity exec \
  -B /scratch:/scratch -B /project:/project "$SIF" \
  python3 "$KIT/verifier_batch.py" --url "http://127.0.0.1:$PORT" --model "$MODEL_TAG" \
    --items "$ITEMS" --answers "$ANSWERS" --mode refnum --n "$N" --conc "$CONC" \
    --out "$OUT/v12_refnum_${MODEL_TAG}_$SLURM_JOB_ID.jsonl"

cat > "$OUT/e12b_cmp_$SLURM_JOB_ID.py" <<'PY'
import json, os, sys
OUT, JOB = sys.argv[1], sys.argv[2]
sys.path.insert(0, "/project/project_465003647/gama/bench_v2")
from score_honesty_real import classify
items = {x["id"]: x for x in (json.loads(l) for l in open(os.path.join(OUT, "..", "bench_v2", "items_honesty_real.jsonl"), encoding="utf-8") if l.strip())}
ans = {x["id"]: (x.get("text") or "").strip()
       for x in (json.loads(l) for l in open(os.path.join(OUT, "v2hr_qwen_s42_23623454.jsonl"), encoding="utf-8") if l.strip())}
truth = {i: classify(items[i], ans[i]) for i in items if i in ans}
v = {r["id"]: r for r in (json.loads(l) for l in open(os.path.join(OUT, f"v12_refnum_{sys.argv[3]}_{JOB}.jsonl"), encoding="utf-8") if l.strip())}
fab = [i for i in truth if truth[i] == "FABRICATE" and i in v]
cor = [i for i in truth if truth[i] == "CORRECT" and i in v]
det = sum(1 for i in fab if v[i]["verdict"] == "NETACNO")
fa = sum(1 for i in cor if v[i]["verdict"] == "NETACNO")
res = {"arm": "self_refnum", "fabrications": len(fab), "detected": det,
       "detection_rate": round(det / len(fab), 4) if fab else None,
       "correct_claims": len(cor), "false_alarms": fa,
       "false_alarm_rate": round(fa / len(cor), 4) if cor else None}
json.dump(res, open(os.path.join(OUT, f"e12b_refnum_{JOB}.json"), "w"), indent=2)
print(json.dumps(res, indent=2))
PY
srun --overlap --jobid="$SLURM_JOB_ID" -n1 --cpus-per-task=4 singularity exec \
  -B /scratch:/scratch -B /project:/project "$SIF" \
  python3 "$OUT/e12b_cmp_$SLURM_JOB_ID.py" "$OUT" "$SLURM_JOB_ID" "$MODEL_TAG"
echo "E12B_DONE $(date -u)"
