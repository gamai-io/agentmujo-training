#!/bin/bash
# bal6 honesty_real: baseline for the dose-response (bal6 = 2 epochs, bal7 = 4 epochs).
# Serves the already-merged bal6 adapter and runs the 500 real-entity items (protocol A).
#SBATCH --job-name=amj_bal6hr
#SBATCH --account=project_465003647
#SBATCH --partition=dev-g
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=56
#SBATCH --gres=gpu:mi250:4
#SBATCH --time=00:40:00
#SBATCH --output=/project/project_465003647/gama/out/bal6hr_%j.out
set -uo pipefail
G=/project/project_465003647/gama
KIT=$G/bench_v2
OUT=$G/out
SIF=/appl/local/laifs/containers/lumi-multitorch-latest.sif
MERGED=/scratch/project_465003647/agentmujo9b/out/run_bal6/merged
CACHE_ROOT=${VLLM_CACHE_ROOT:-/scratch/project_465003647/vllm_cache}
export VLLM_CACHE_ROOT="$CACHE_ROOT" SINGULARITYENV_VLLM_CACHE_ROOT="$CACHE_ROOT"
export TRITON_CACHE_DIR="$CACHE_ROOT/triton" SINGULARITYENV_TRITON_CACHE_DIR="$CACHE_ROOT/triton"
export HF_HUB_CACHE=/scratch/project_465003647/agentmujo/hfcache
export SINGULARITYENV_HF_HUB_CACHE=/scratch/project_465003647/agentmujo/hfcache
export NO_THINK=1 SINGULARITYENV_NO_THINK=1
mkdir -p "$CACHE_ROOT/triton" "$OUT"
echo "HOST=$(hostname) DATE=$(date -u) MERGED=$MERGED"
[ -d "$MERGED" ] || { echo MISSING_MERGED; exit 3; }

srun -n1 --gres=gpu:mi250:4 --cpus-per-task=32 singularity exec \
  -B /pfs:/pfs -B /scratch:/scratch -B /project:/project "$SIF" \
  python -m vllm.entrypoints.openai.api_server \
    --model "$MERGED" --served-model-name bal6 --host 127.0.0.1 --port 8000 \
    --tensor-parallel-size 4 --max-model-len 8192 --max-num-seqs 256 \
    --gpu-memory-utilization 0.90 \
    > "$OUT/vllm_bal6hr_$SLURM_JOB_ID.log" 2>&1 &
for i in $(seq 1 450); do curl -sf http://127.0.0.1:8000/v1/models >/dev/null && break; sleep 2; done
curl -sf http://127.0.0.1:8000/v1/models >/dev/null || { echo VLLM_FAIL; tail -30 "$OUT/vllm_bal6hr_$SLURM_JOB_ID.log"; exit 4; }
echo VLLM_READY

srun --overlap --jobid="$SLURM_JOB_ID" -n1 --cpus-per-task=16 singularity exec \
  -B /pfs:/pfs -B /scratch:/scratch -B /project:/project "$SIF" \
  python3 "$KIT/run_v2.py" --url http://127.0.0.1:8000 --model bal6 \
    --items "$KIT/items_honesty_real.jsonl" --n 0 --conc 64 --max-tokens 128 \
    --out "$OUT/v2hr_bal6_$SLURM_JOB_ID.jsonl" --summary "$OUT/v2hr_bal6_$SLURM_JOB_ID.summary.json"

srun --overlap --jobid="$SLURM_JOB_ID" -n1 --cpus-per-task=4 singularity exec \
  -B /pfs:/pfs -B /scratch:/scratch -B /project:/project "$SIF" \
  python3 "$KIT/score_honesty_real.py" --items "$KIT/items_honesty_real.jsonl" \
    --results "$OUT/v2hr_bal6_$SLURM_JOB_ID.jsonl" --out "$OUT/honesty_real_bal6_$SLURM_JOB_ID.json"
echo BAL6HR_DONE
