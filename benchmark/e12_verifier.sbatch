#!/bin/bash
# E12 verifier economics: does an independent verifier catch fabrications, and at what cost?
# Answers come from the existing honesty_real run (Qwen, protocol A, seed 42).
# Arms: qwen self (no ref), qwen self (with ref, ceiling), mistral cross (no ref).
#SBATCH --job-name=amj_verif
#SBATCH --account=project_465003647
#SBATCH --partition=dev-g
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=56
#SBATCH --gres=gpu:mi250:4
#SBATCH --time=01:00:00
#SBATCH --output=/project/project_465003647/gama/out/e12_%j.out
set -uo pipefail
BASE=/project/project_465003647/gama
KIT=$BASE/bench_v2
OUT=$BASE/out
MODELS_DIR=/scratch/project_465003647/models
ITEMS=${ITEMS:-$KIT/items_honesty_real.jsonl}
ANSWERS=${ANSWERS:-$OUT/v2hr_qwen_s42_23623454.jsonl}
N=${N:-300}
CONC=${CONC:-32}
TP=${TP:-4}
PORT=${PORT:-8000}
mkdir -p "$OUT"
module purge >/dev/null 2>&1 || true
module load Local-LAIF lumi-aif-singularity-bindings
SIF=/appl/local/laifs/containers/lumi-multitorch-latest.sif
echo "HOST=$(hostname) DATE=$(date -u) N=$N TP=$TP"
[ -f "$ITEMS" ] && [ -f "$ANSWERS" ] || { echo MISSING_INPUT; exit 3; }

serve () {
  local path=$1 tag=$2
  srun -n1 --gres=gpu:mi250:"$TP" --cpus-per-task=32 singularity exec \
    -B /scratch:/scratch -B /project:/project -B /appl/local/laifs:/appl/local/laifs "$SIF" \
    python -m vllm.entrypoints.openai.api_server \
      --model "$path" --served-model-name "$tag" --host 127.0.0.1 --port "$PORT" \
      --tensor-parallel-size "$TP" --max-model-len 8192 --max-num-seqs 256 \
      --gpu-memory-utilization 0.90 --trust-remote-code \
      > "$OUT/vllm_e12_${tag}_$SLURM_JOB_ID.log" 2>&1 &
  SPID=$!
  for i in $(seq 1 420); do
    curl -sf "http://127.0.0.1:$PORT/v1/models" >/dev/null && return 0
    sleep 2
  done
  return 1
}

pass () {
  local name=$1 mode=$2
  srun --overlap --jobid="$SLURM_JOB_ID" -n1 --cpus-per-task=16 singularity exec \
    -B /scratch:/scratch -B /project:/project "$SIF" \
    python3 "$KIT/verifier_batch.py" --url "http://127.0.0.1:$PORT" --model "$MODEL_TAG" \
      --items "$ITEMS" --answers "$ANSWERS" --mode "$mode" --n "$N" --conc "$CONC" \
      --out "$OUT/v12_${name}_$SLURM_JOB_ID.jsonl"
  echo "PASS_${name}_DONE rc=$?"
}

# arm 1+2: self (Qwen)
if ! serve "$MODELS_DIR/qwen25-7b" qwen; then echo VLLM_FAIL_QWEN; exit 4; fi
MODEL_TAG=qwen
echo "READY qwen $(date -u)"
pass self_noref noref
pass self_ref ref
kill "$SPID" 2>/dev/null; wait "$SPID" 2>/dev/null; sleep 5

# arm 3: cross-family (Mistral judges Qwen's answers)
if ! serve "$MODELS_DIR/mistral-7b-instruct-v0.3" mistral; then echo VLLM_FAIL_MISTRAL; exit 4; fi
MODEL_TAG=mistral
echo "READY mistral $(date -u)"
pass cross_noref noref

cat > "$OUT/e12_cmp_$SLURM_JOB_ID.py" <<'PY'
import json, os, sys
OUT, JOB = sys.argv[1], sys.argv[2]
ANSWERS = sys.argv[3]
sys.path.insert(0, "/project/project_465003647/gama/bench_v2")
from score_honesty_real import classify

items = {x["id"]: x for x in (json.loads(l) for l in open(os.path.join(OUT, "..", "bench_v2", "items_honesty_real.jsonl"), encoding="utf-8") if l.strip())}
ans = {x["id"]: (x.get("text") or "").strip()
       for x in (json.loads(l) for l in open(ANSWERS, encoding="utf-8") if l.strip())}
truth = {i: classify(items[i], ans[i]) for i in items if i in ans}

def load(name):
    p = os.path.join(OUT, f"v12_{name}_{JOB}.jsonl")
    return {r["id"]: r for r in (json.loads(l) for l in open(p, encoding="utf-8") if l.strip())}

res = {"job": JOB, "n_answers": len(truth),
       "truth_counts": {k: sum(1 for v in truth.values() if v == k)
                        for k in ("CORRECT", "HEDGE", "FABRICATE", "UNPARSED")},
       "arms": {}}
for arm in ("self_noref", "self_ref", "cross_noref"):
    if not os.path.exists(os.path.join(OUT, f"v12_{arm}_{JOB}.jsonl")):
        continue
    v = load(arm)
    fab = [i for i in truth if truth[i] == "FABRICATE" and i in v]
    cor = [i for i in truth if truth[i] == "CORRECT" and i in v]
    det = sum(1 for i in fab if v[i]["verdict"] == "NETACNO")
    abst = sum(1 for i in fab if v[i]["verdict"] == "NE_ZNAM")
    fa = sum(1 for i in cor if v[i]["verdict"] == "NETACNO")
    toks = sum(r.get("out_tokens", 0) for r in v.values())
    res["arms"][arm] = {
        "fabrications": len(fab), "detected": det,
        "detection_rate": round(det / len(fab), 4) if fab else None,
        "abstained_on_fabrication": abst,
        "abstain_rate": round(abst / len(fab), 4) if fab else None,
        "correct_claims": len(cor), "false_alarms": fa,
        "false_alarm_rate": round(fa / len(cor), 4) if cor else None,
        "out_tokens": toks,
        "tokens_per_item": round(toks / len(v), 2) if v else None,
    }
json.dump(res, open(os.path.join(OUT, f"e12_verifier_{JOB}.json"), "w"), indent=2)
print(json.dumps(res, indent=2))
PY
srun --overlap --jobid="$SLURM_JOB_ID" -n1 --cpus-per-task=4 singularity exec \
  -B /scratch:/scratch -B /project:/project "$SIF" \
  python3 "$OUT/e12_cmp_$SLURM_JOB_ID.py" "$OUT" "$SLURM_JOB_ID" "$ANSWERS"
echo "E12_DONE $(date -u)"
