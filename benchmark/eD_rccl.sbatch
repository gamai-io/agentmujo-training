#!/bin/bash
# E-D: RCCL ALGO/PROTO/LAUNCH_ORDER sweep at TP=8 with BI=1, two processes per config.
# Prereg: PREREG_E_D_RCCL_2026-11-11.md
#SBATCH --job-name=amj_eD_rccl
#SBATCH --account=project_465003647
#SBATCH --partition=small-g
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=56
#SBATCH --gres=gpu:mi250:8
#SBATCH --time=01:30:00
#SBATCH --output=/project/project_465003647/gama/out/eD_rccl_%j.out
set -uo pipefail
BASE=/project/project_465003647/gama; KIT=$BASE/bench_v2; OUT=$BASE/out
MODEL=${MODEL:-/scratch/project_465003647/models/mistral-7b-instruct-v0.3}
REPS=${REPS:-1}; MAXTOK=${MAXTOK:-128}; J=$SLURM_JOB_ID
mkdir -p "$OUT"
module purge >/dev/null 2>&1 || true
module load Local-LAIF lumi-aif-singularity-bindings
SIF=/appl/local/laifs/containers/lumi-multitorch-latest.sif
CACHE=/scratch/project_465003647/vllm_cache
export VLLM_CACHE_ROOT="$CACHE" TRITON_CACHE_DIR="$CACHE/triton"
export SINGULARITYENV_VLLM_CACHE_ROOT="$CACHE" SINGULARITYENV_TRITON_CACHE_DIR="$CACHE/triton"
echo "HOST=$(hostname) DATE=$(date -u) MODEL=$MODEL TP=8 BI=1 REPS=$REPS"
rocm-smi 2>/dev/null | head -4 || true
serve () { # tag port
  local tag=$1 port=$2
  srun -n1 --gres=gpu:mi250:8 --cpus-per-task=32 singularity exec \
    -B /scratch:/scratch -B /project:/project -B /appl/local/laifs:/appl/local/laifs "$SIF" \
    python -m vllm.entrypoints.openai.api_server --model "$MODEL" --served-model-name qwen \
      --host 127.0.0.1 --port "$port" --tensor-parallel-size 8 --max-model-len 4096 \
      --max-num-seqs 64 --gpu-memory-utilization 0.90 --trust-remote-code \
      > "$OUT/eD_vllm_${tag}_$J.log" 2>&1 &
  SPID=$!
  for i in $(seq 1 300); do curl -sf "http://127.0.0.1:$port/v1/models" >/dev/null && return 0; sleep 2; done
  return 1
}
stop () { kill "$SPID" 2>/dev/null; wait "$SPID" 2>/dev/null; sleep 6; }
runcell () { # tag port ref
  local tag=$1 port=$2 ref=${3:-}; local extra=""
  [ -n "$ref" ] && extra="--reference $ref"
  srun --overlap --jobid="$J" -n1 --cpus-per-task=8 singularity exec \
    -B /scratch:/scratch -B /project:/project "$SIF" \
    python3 "$KIT/eA_atlas.py" --url "http://127.0.0.1:$port" --model qwen --batch 1 \
      --reps "$REPS" --max-tokens "$MAXTOK" --tag "$tag" \
      --out "$OUT/eD_${tag}_$J.jsonl" --summary "$OUT/eD_${tag}_$J.summary.json" $extra
}
setenv () { # algo proto order
  unset NCCL_ALGO NCCL_PROTO NCCL_LAUNCH_ORDER_IMPLICIT SINGULARITYENV_NCCL_ALGO SINGULARITYENV_NCCL_PROTO SINGULARITYENV_NCCL_LAUNCH_ORDER_IMPLICIT
  if [ -n "${1:-}" ]; then
    export NCCL_ALGO="$1" NCCL_PROTO="$2" NCCL_LAUNCH_ORDER_IMPLICIT="$3"
    export SINGULARITYENV_NCCL_ALGO="$1" SINGULARITYENV_NCCL_PROTO="$2" SINGULARITYENV_NCCL_LAUNCH_ORDER_IMPLICIT="$3"
  fi
}
export VLLM_BATCH_INVARIANT=1 SINGULARITYENV_VLLM_BATCH_INVARIANT=1
PORT=8021
run_cfg () { # tag algo proto order
  local tag=$1 a=${2:-} p=${3:-} o=${4:-}
  setenv "$a" "$p" "$o"
  echo "CFG $tag ALGO=${a:-auto} PROTO=${p:-auto} ORDER=${o:-auto}"
  if ! serve "${tag}_r1" "$PORT"; then echo "CFG_FAIL $tag r1"; tail -5 "$OUT/eD_vllm_${tag}_r1_$J.log"; return 1; fi
  runcell "${tag}_r1" "$PORT"
  stop
  if ! serve "${tag}_r2" "$PORT"; then echo "CFG_FAIL $tag r2"; tail -5 "$OUT/eD_vllm_${tag}_r2_$J.log"; return 1; fi
  runcell "${tag}_r2" "$PORT" "$OUT/eD_${tag}_r1_$J.jsonl"
  stop
}
run_cfg base
for O in 0 1; do
  for A in Ring Tree; do
    for P in Simple LL128; do
      run_cfg "rccl_${A}_${P}_${O}" "$A" "$P" "$O" || true
    done
  done
done
echo "E_D_RCCL_DONE $(date -u)"
sha256sum "$OUT"/eD_*_$J.summary.json > "$OUT/eD_SHA256SUMS_$J.txt" 2>/dev/null || true
cat "$OUT/eD_SHA256SUMS_$J.txt" || true
