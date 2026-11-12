#!/bin/bash
# E-E: 5 restarts per RCCL config at TP=8, BI=1; compare each to run1.
#SBATCH --job-name=amj_eE_restartN
#SBATCH --account=project_465003647
#SBATCH --partition=dev-g
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=56
#SBATCH --gres=gpu:mi250:8
#SBATCH --time=02:00:00
#SBATCH --output=/project/project_465003647/gama/out/eE_restartN_%j.out
set -uo pipefail
BASE=/project/project_465003647/gama; KIT=$BASE/bench_v2; OUT=$BASE/out
MODEL=${MODEL:-/scratch/project_465003647/models/mistral-7b-instruct-v0.3}
REPS=1; MAXTOK=128; J=$SLURM_JOB_ID; N=5
mkdir -p "$OUT"
module purge >/dev/null 2>&1 || true
module load Local-LAIF lumi-aif-singularity-bindings
SIF=/appl/local/laifs/containers/lumi-multitorch-latest.sif
CACHE=/scratch/project_465003647/vllm_cache
export VLLM_CACHE_ROOT="$CACHE" TRITON_CACHE_DIR="$CACHE/triton"
export SINGULARITYENV_VLLM_CACHE_ROOT="$CACHE" SINGULARITYENV_TRITON_CACHE_DIR="$CACHE/triton"
export VLLM_BATCH_INVARIANT=1 SINGULARITYENV_VLLM_BATCH_INVARIANT=1
echo "HOST=$(hostname) DATE=$(date -u) MODEL=$MODEL"
serve () {
  local tag=$1 port=$2
  srun -n1 --gres=gpu:mi250:8 --cpus-per-task=32 singularity exec \
    -B /scratch:/scratch -B /project:/project -B /appl/local/laifs:/appl/local/laifs "$SIF" \
    python -m vllm.entrypoints.openai.api_server --model "$MODEL" --served-model-name qwen \
      --host 127.0.0.1 --port "$port" --tensor-parallel-size 8 --max-model-len 4096 \
      --max-num-seqs 64 --gpu-memory-utilization 0.90 --trust-remote-code \
      > "$OUT/eE_vllm_${tag}_$J.log" 2>&1 &
  SPID=$!
  local i; for i in $(seq 1 300); do curl -sf "http://127.0.0.1:$port/v1/models" >/dev/null && return 0; sleep 2; done
  return 1
}
stop () { kill "$SPID" 2>/dev/null; wait "$SPID" 2>/dev/null; sleep 6; }
runcell () {
  local tag=$1 port=$2 ref=${3:-}; local extra=""
  [ -n "$ref" ] && extra="--reference $ref"
  srun --overlap --jobid="$J" -n1 --cpus-per-task=8 singularity exec \
    -B /scratch:/scratch -B /project:/project "$SIF" \
    python3 "$KIT/eA_atlas.py" --url "http://127.0.0.1:$port" --model qwen --batch 1 \
      --reps "$REPS" --max-tokens "$MAXTOK" --tag "$tag" \
      --out "$OUT/eE_${tag}_$J.jsonl" --summary "$OUT/eE_${tag}_$J.summary.json" $extra
}
setenv () {
  unset NCCL_ALGO NCCL_PROTO SINGULARITYENV_NCCL_ALGO SINGULARITYENV_NCCL_PROTO
  if [ -n "${1:-}" ]; then
    export NCCL_ALGO="$1" NCCL_PROTO="$2"
    export SINGULARITYENV_NCCL_ALGO="$1" SINGULARITYENV_NCCL_PROTO="$2"
  fi
}
PORT=8031
run_cfg () {
  local tag=$1 a=${2:-} p=${3:-}
  setenv "$a" "$p"
  echo "CFG $tag ALGO=${a:-auto} PROTO=${p:-auto}"
  if ! serve "${tag}_r1" "$PORT"; then echo "CFG_FAIL $tag r1"; return 1; fi
  runcell "${tag}_r1" "$PORT"
  stop
  local k; for k in $(seq 2 $((N+1))); do
    if ! serve "${tag}_r${k}" "$PORT"; then echo "CFG_FAIL $tag r${k}"; continue; fi
    runcell "${tag}_r${k}" "$PORT" "$OUT/eE_${tag}_r1_$J.jsonl"
    stop
  done
}
run_cfg base
run_cfg ring_simple Ring Simple
run_cfg tree_simple Tree Simple
echo "E_E_DONE $(date -u)"
sha256sum "$OUT"/eE_*_$J.summary.json > "$OUT/eE_SHA256SUMS_$J.txt" 2>/dev/null || true
cat "$OUT/eE_SHA256SUMS_$J.txt" || true
