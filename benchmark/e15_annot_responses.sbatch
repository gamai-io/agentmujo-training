#!/bin/bash
# E15: produce model answers for the 200-item human-eval kit, then build items_annot.jsonl.
# Needed to run the real human evaluation (100 fictitious + 100 real, with references).
#SBATCH --job-name=amj_annot
#SBATCH --account=project_465003647
#SBATCH --partition=dev-g
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=56
#SBATCH --gres=gpu:mi250:4
#SBATCH --time=00:40:00
#SBATCH --output=/project/project_465003647/gama/out/e15_%j.out
set -uo pipefail
BASE=/project/project_465003647/gama
KIT=$BASE/bench_v2
OUT=$BASE/out
MODEL=${MODEL:-/scratch/project_465003647/models/qwen25-7b}
TAG=${TAG:-qwen}
ITEMS=${ITEMS:-$KIT/items_200.jsonl}
ANNOT_OUT=${ANNOT_OUT:-$KIT/items_annot.jsonl}
TP=${TP:-4}
PORT=${PORT:-8000}
module purge >/dev/null 2>&1 || true
module load Local-LAIF lumi-aif-singularity-bindings
SIF=/appl/local/laifs/containers/lumi-multitorch-latest.sif
CACHE_ROOT=${VLLM_CACHE_ROOT:-/scratch/project_465003647/vllm_cache}
export VLLM_CACHE_ROOT="$CACHE_ROOT" SINGULARITYENV_VLLM_CACHE_ROOT="$CACHE_ROOT"
export TRITON_CACHE_DIR="$CACHE_ROOT/triton" SINGULARITYENV_TRITON_CACHE_DIR="$CACHE_ROOT/triton"
mkdir -p "$CACHE_ROOT/triton" "$OUT"
echo "HOST=$(hostname) DATE=$(date -u) ITEMS=$ITEMS"
[ -f "$ITEMS" ] || { echo MISSING_ITEMS; exit 3; }

srun -n1 --gres=gpu:mi250:"$TP" --cpus-per-task=32 singularity exec \
  -B /scratch:/scratch -B /project:/project -B /appl/local/laifs:/appl/local/laifs "$SIF" \
  python -m vllm.entrypoints.openai.api_server \
    --model "$MODEL" --served-model-name "$TAG" --host 127.0.0.1 --port "$PORT" \
    --tensor-parallel-size "$TP" --max-model-len 8192 --max-num-seqs 256 \
    --gpu-memory-utilization 0.90 --trust-remote-code \
    > "$OUT/vllm_e15_$SLURM_JOB_ID.log" 2>&1 &
SPID=$!
for i in $(seq 1 420); do curl -sf "http://127.0.0.1:$PORT/v1/models" >/dev/null && break; sleep 2; done
curl -sf "http://127.0.0.1:$PORT/v1/models" >/dev/null || { echo VLLM_FAIL; exit 4; }
echo "READY $(date -u)"

srun --overlap --jobid="$SLURM_JOB_ID" -n1 --cpus-per-task=16 singularity exec \
  -B /scratch:/scratch -B /project:/project "$SIF" \
  python3 "$KIT/run_v2.py" --url "http://127.0.0.1:$PORT" --model "$TAG" \
    --items "$ITEMS" --n 0 --conc 32 --max-tokens 128 \
    --out "$OUT/v2annot_${TAG}_$SLURM_JOB_ID.jsonl" \
    --summary "$OUT/v2annot_${TAG}_$SLURM_JOB_ID.summary.json"

srun --overlap --jobid="$SLURM_JOB_ID" -n1 --cpus-per-task=4 singularity exec \
  -B /scratch:/scratch -B /project:/project "$SIF" \
  python3 "$KIT/make_annot_full.py" --items "$ITEMS" \
    --responses "$OUT/v2annot_${TAG}_$SLURM_JOB_ID.jsonl" \
    --out "$ANNOT_OUT"
echo "E15_DONE $(date -u)"
