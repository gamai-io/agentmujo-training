#!/bin/bash
# E-A smoke: TP1, default vs VLLM_BATCH_INVARIANT=1; B=1 reference vs B=8.
# Prereg: PREREG_E_A_2026-11-11.md (sha256 dea58fd4...)
#SBATCH --job-name=amj_eA_smoke
#SBATCH --account=project_465003647
#SBATCH --partition=dev-g
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=56
#SBATCH --gres=gpu:mi250:4
#SBATCH --time=01:00:00
#SBATCH --output=/project/project_465003647/gama/out/eA_smoke_%j.out
set -uo pipefail
BASE=/project/project_465003647/gama
KIT=$BASE/bench_v2
OUT=$BASE/out
MODEL=${MODEL:-/scratch/project_465003647/models/qwen25-7b}
TP=${TP:-1}
PORT=${PORT:-8001}
REPS=${REPS:-3}
MAXTOK=${MAXTOK:-128}
J=$SLURM_JOB_ID
mkdir -p "$OUT"
module purge >/dev/null 2>&1 || true
module load Local-LAIF lumi-aif-singularity-bindings
SIF=/appl/local/laifs/containers/lumi-multitorch-latest.sif
CACHE_ROOT=/scratch/project_465003647/vllm_cache
export VLLM_CACHE_ROOT="$CACHE_ROOT" TRITON_CACHE_DIR="$CACHE_ROOT/triton"
export SINGULARITYENV_VLLM_CACHE_ROOT="$CACHE_ROOT" SINGULARITYENV_TRITON_CACHE_DIR="$CACHE_ROOT/triton"
echo "HOST=$(hostname) DATE=$(date -u) TP=$TP MODEL=$MODEL"
rocm-smi 2>/dev/null | head -6 || true
serve () {
  local tag=$1 bi=$2
  export VLLM_BATCH_INVARIANT="$bi" SINGULARITYENV_VLLM_BATCH_INVARIANT="$bi"
  srun -n1 --gres=gpu:mi250:"$TP" --cpus-per-task=32 singularity exec \
    -B /scratch:/scratch -B /project:/project -B /appl/local/laifs:/appl/local/laifs "$SIF" \
    python -m vllm.entrypoints.openai.api_server \
      --model "$MODEL" --served-model-name qwen --host 127.0.0.1 --port "$PORT" \
      --tensor-parallel-size "$TP" --max-model-len 4096 --max-num-seqs 64 \
      --gpu-memory-utilization 0.90 --trust-remote-code \
      > "$OUT/eA_vllm_${tag}_$J.log" 2>&1 &
  SPID=$!
  for i in $(seq 1 300); do
    curl -sf "http://127.0.0.1:$PORT/v1/models" >/dev/null && return 0
    sleep 2
  done
  return 1
}
stop () { kill "$SPID" 2>/dev/null; wait "$SPID" 2>/dev/null; sleep 6; }
runcell () {
  local tag=$1 b=$2 ref=${3:-}
  local extra=""
  [ -n "$ref" ] && extra="--reference $ref"
  srun --overlap --jobid="$J" -n1 --cpus-per-task=8 singularity exec \
    -B /scratch:/scratch -B /project:/project "$SIF" \
    python3 "$KIT/eA_atlas.py" --url "http://127.0.0.1:$PORT" --model qwen \
      --batch "$b" --reps "$REPS" --max-tokens "$MAXTOK" --tag "$tag" \
      --out "$OUT/eA_${tag}_b${b}_$J.jsonl" --summary "$OUT/eA_${tag}_b${b}_$J.summary.json" $extra
}
# arm 1: default
if ! serve def 0; then echo VLLM_FAIL_DEF; tail -30 "$OUT/eA_vllm_def_$J.log"; exit 3; fi
echo "READY_DEF $(date -u)"
runcell def 1
runcell def 8 "$OUT/eA_def_b1_$J.jsonl"
stop
# arm 2: batch invariant
if ! serve bi 1; then echo VLLM_FAIL_BI; tail -30 "$OUT/eA_vllm_bi_$J.log"; exit 3; fi
echo "READY_BI $(date -u)"
grep -i "batch.invarian" "$OUT/eA_vllm_bi_$J.log" | head -3 || true
runcell bi 1
runcell bi 8 "$OUT/eA_bi_b1_$J.jsonl"
stop
echo "E_A_SMOKE_DONE $(date -u)"
sha256sum "$OUT"/eA_*_$J.json "$OUT"/eA_*_$J.jsonl > "$OUT/eA_SHA256SUMS_$J.txt" 2>/dev/null || true
cat "$OUT/eA_SHA256SUMS_$J.txt" || true
