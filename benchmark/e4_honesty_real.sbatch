#!/bin/bash
#SBATCH --job-name=amj_honreal
#SBATCH --account=project_465003647
#SBATCH --partition=dev-g
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=56
#SBATCH --gres=gpu:mi250:4
#SBATCH --time=01:30:00
#SBATCH --output=/project/project_465003647/gama/out/honreal_%j.out
set -uo pipefail
BASE=/project/project_465003647/gama
KIT=$BASE/bench_v2
OUT=$BASE/out
MODELS_DIR=/scratch/project_465003647/models
ITEMS=${ITEMS:-$KIT/items_honesty_real.jsonl}
SEEDS=${SEEDS:-42 43}
TP=${TP:-4}
PORT=${PORT:-8000}
MAXTOK=${MAXTOK:-128}
NO_THINK=${NO_THINK:-0}
export NO_THINK
export SINGULARITYENV_NO_THINK="$NO_THINK"
mkdir -p "$OUT"
module purge >/dev/null 2>&1 || true
module load Local-LAIF lumi-aif-singularity-bindings
SIF=/appl/local/laifs/containers/lumi-multitorch-latest.sif

echo "HOST=$(hostname) DATE=$(date -u) ITEMS=$ITEMS SEEDS=$SEEDS NO_THINK=$NO_THINK"
[ -f "$ITEMS" ] || { echo MISSING_ITEMS; exit 3; }
sha256sum "$ITEMS"

for spec in "qwen25-7b:qwen" "mistral-7b-instruct-v0.3:mistral" "phi35-mini-instruct:phi35"; do
  M="${spec%%:*}"; TAG="${spec##*:}"
  MPATH="$MODELS_DIR/$M"
  [ -d "$MPATH" ] || { echo "MISSING_MODEL $MPATH"; continue; }
  echo "=== MODEL $TAG $(date -u)"
  srun -n1 --gres=gpu:mi250:"$TP" --cpus-per-task=32 singularity exec \
    -B /scratch:/scratch -B /project:/project -B /appl/local/laifs:/appl/local/laifs "$SIF" \
    python -m vllm.entrypoints.openai.api_server \
      --model "$MPATH" --served-model-name "$TAG" --host 127.0.0.1 --port "$PORT" \
      --tensor-parallel-size "$TP" --max-model-len 8192 --max-num-seqs 128 \
      --gpu-memory-utilization 0.90 --trust-remote-code \
      > "$OUT/vllm_hr_${TAG}_$SLURM_JOB_ID.log" 2>&1 &
  SPID=$!
  ok=0
  for i in $(seq 1 360); do
    if curl -sf "http://127.0.0.1:$PORT/v1/models" >/dev/null; then ok=1; break; fi
    sleep 2
  done
  if [ "$ok" != 1 ]; then
    echo "VLLM_FAIL $TAG"; tail -20 "$OUT/vllm_hr_${TAG}_$SLURM_JOB_ID.log"
    kill "$SPID" 2>/dev/null; continue
  fi
  echo "VLLM_READY $TAG $(date -u)"
  for S in $SEEDS; do
    srun --overlap --jobid="$SLURM_JOB_ID" -n1 --cpus-per-task=16 singularity exec \
      -B /scratch:/scratch -B /project:/project "$SIF" \
      python3 "$KIT/run_v2.py" --url "http://127.0.0.1:$PORT" --model "$TAG" \
        --items "$ITEMS" --n 0 --conc 64 --max-tokens "$MAXTOK" \
        --out "$OUT/v2hr_${TAG}_s${S}_$SLURM_JOB_ID.jsonl" \
        --summary "$OUT/v2hr_${TAG}_s${S}_$SLURM_JOB_ID.summary.json"
    srun --overlap --jobid="$SLURM_JOB_ID" -n1 --cpus-per-task=4 singularity exec \
      -B /scratch:/scratch -B /project:/project "$SIF" \
      python3 "$KIT/score_honesty_real.py" --items "$ITEMS" \
        --results "$OUT/v2hr_${TAG}_s${S}_$SLURM_JOB_ID.jsonl" \
        --out "$OUT/honesty_real_${TAG}_s${S}_$SLURM_JOB_ID.json"
    echo "SCORED $TAG seed=$S"
  done
  kill "$SPID" 2>/dev/null; wait "$SPID" 2>/dev/null; sleep 5
done
echo "HONREAL_DONE $(date -u)"
