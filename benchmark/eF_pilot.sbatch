#!/bin/bash
# E-F pilot: false-success claim-vs-probe on local file tasks; 2 models x 2 policies x 10 tasks.
#SBATCH --job-name=amj_eF_pilot
#SBATCH --account=project_465003647
#SBATCH --partition=dev-g
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=56
#SBATCH --gres=gpu:mi250:4
#SBATCH --time=01:00:00
#SBATCH --output=/project/project_465003647/gama/out/eF_pilot_%j.out
set -uo pipefail
BASE=/project/project_465003647/gama; KIT=$BASE/bench_v2; OUT=$BASE/out
J=$SLURM_JOB_ID; PORT=8041
WORK=/scratch/project_465003647/eF/$J
mkdir -p "$OUT" "$WORK"
module purge >/dev/null 2>&1 || true
module load Local-LAIF lumi-aif-singularity-bindings
SIF=/appl/local/laifs/containers/lumi-multitorch-latest.sif
CACHE=/scratch/project_465003647/vllm_cache
export VLLM_CACHE_ROOT="$CACHE" TRITON_CACHE_DIR="$CACHE/triton"
export SINGULARITYENV_VLLM_CACHE_ROOT="$CACHE" SINGULARITYENV_TRITON_CACHE_DIR="$CACHE/triton"
echo "HOST=$(hostname) DATE=$(date -u) WORK=$WORK"
serve () {
  local tag=$1 model=$2
  srun -n1 --gres=gpu:mi250:4 --cpus-per-task=32 singularity exec \
    -B /scratch:/scratch -B /project:/project -B /appl/local/laifs:/appl/local/laifs "$SIF" \
    python -m vllm.entrypoints.openai.api_server --model "$model" --served-model-name m \
      --host 127.0.0.1 --port "$PORT" --tensor-parallel-size 4 --max-model-len 4096 \
      --max-num-seqs 16 --gpu-memory-utilization 0.90 --trust-remote-code \
      > "$OUT/eF_vllm_${tag}_$J.log" 2>&1 &
  SPID=$!
  for i in $(seq 1 300); do curl -sf "http://127.0.0.1:$PORT/v1/models" >/dev/null && return 0; sleep 2; done
  return 1
}
stop () { kill "$SPID" 2>/dev/null; wait "$SPID" 2>/dev/null; sleep 6; }
run_model () {
  local tag=$1 model=$2
  if ! serve "$tag" "$model"; then echo "MODEL_FAIL $tag"; tail -10 "$OUT/eF_vllm_${tag}_$J.log"; return 1; fi
  echo "READY $tag $(date -u)"
  srun --overlap --jobid="$J" -n1 --cpus-per-task=8 singularity exec \
    -B /scratch:/scratch -B /project:/project "$SIF" \
    python3 "$KIT/eF_agent.py" --url "http://127.0.0.1:$PORT" --model m \
      --workroot "$WORK/$tag" --policy both --out "$OUT/eF_${tag}_$J.jsonl"
  stop
}
run_model qwen /scratch/project_465003647/models/qwen25-7b
run_model mistral /scratch/project_465003647/models/mistral-7b-instruct-v0.3
echo "E_F_DONE $(date -u)"
sha256sum "$OUT"/eF_*_$J.jsonl > "$OUT/eF_SHA256SUMS_$J.txt" 2>/dev/null || true
cat "$OUT/eF_SHA256SUMS_$J.txt" || true
