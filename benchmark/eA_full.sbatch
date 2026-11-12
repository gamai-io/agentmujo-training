#!/bin/bash
# E-A full: TP {1,4} x B {1,2,8,32} x arm {default, BI, TRITON_ATTN, BI+TRITON}
# Prereg: PREREG_E_A_2026-11-11.md. Pilot: RESULTS_E_A_PILOT_2026-11-11.md.
#SBATCH --job-name=amj_eA_full
#SBATCH --account=project_465003647
#SBATCH --partition=dev-g
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=56
#SBATCH --gres=gpu:mi250:4
#SBATCH --time=02:30:00
#SBATCH --output=/project/project_465003647/gama/out/eA_full_%j.out
set -uo pipefail
BASE=/project/project_465003647/gama
KIT=$BASE/bench_v2
OUT=$BASE/out
MODEL=${MODEL:-/scratch/project_465003647/models/qwen25-7b}
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
echo "HOST=$(hostname) DATE=$(date -u) MODEL=$MODEL"
rocm-smi 2>/dev/null | head -6 || true

serve () {
  local tag=$1 tp=$2 bi=$3 backend=$4 port=$5
  export VLLM_BATCH_INVARIANT="$bi" SINGULARITYENV_VLLM_BATCH_INVARIANT="$bi"
  if [ -n "$backend" ]; then
    export VLLM_ATTENTION_BACKEND="$backend" SINGULARITYENV_VLLM_ATTENTION_BACKEND="$backend"
  else
    unset VLLM_ATTENTION_BACKEND SINGULARITYENV_VLLM_ATTENTION_BACKEND
  fi
  srun -n1 --gres=gpu:mi250:"$tp" --cpus-per-task=32 singularity exec \
    -B /scratch:/scratch -B /project:/project -B /appl/local/laifs:/appl/local/laifs "$SIF" \
    python -m vllm.entrypoints.openai.api_server \
      --model "$MODEL" --served-model-name qwen --host 127.0.0.1 --port "$port" \
      --tensor-parallel-size "$tp" --max-model-len 4096 --max-num-seqs 64 \
      --gpu-memory-utilization 0.90 --trust-remote-code \
      > "$OUT/eA_vllm_${tag}_$J.log" 2>&1 &
  SPID=$!
  for i in $(seq 1 360); do
    curl -sf "http://127.0.0.1:$port/v1/models" >/dev/null && return 0
    sleep 2
  done
  return 1
}
stop () { kill "$SPID" 2>/dev/null; wait "$SPID" 2>/dev/null; sleep 6; }
runcell () {
  local tag=$1 b=$2 port=$3 ref=${4:-}
  local extra=""
  [ -n "$ref" ] && extra="--reference $ref"
  srun --overlap --jobid="$J" -n1 --cpus-per-task=8 singularity exec \
    -B /scratch:/scratch -B /project:/project "$SIF" \
    python3 "$KIT/eA_atlas.py" --url "http://127.0.0.1:$port" --model qwen \
      --batch "$b" --reps "$REPS" --max-tokens "$MAXTOK" --tag "$tag" \
      --out "$OUT/eA_${tag}_b${b}_$J.jsonl" --summary "$OUT/eA_${tag}_b${b}_$J.summary.json" $extra
}
run_arm () {
  local name=$1 tp=$2 bi=$3 backend=$4 port=$5
  if ! serve "$name" "$tp" "$bi" "$backend" "$port"; then
    echo "ARM_FAIL $name tp$tp"; tail -20 "$OUT/eA_vllm_${name}_$J.log"; return 1
  fi
  echo "READY $name tp$tp $(date -u)"
  grep -i "batch.invarian" "$OUT/eA_vllm_${name}_$J.log" | head -2 || true
  runcell "$name" 1 "$port"
  for b in 2 8 32; do runcell "$name" "$b" "$port" "$OUT/eA_${name}_b1_$J.jsonl"; done
  stop
}
for TP in 1 4; do
  run_arm "def_tp${TP}"      "$TP" 0 ""             8001 || true
  run_arm "bi_tp${TP}"       "$TP" 1 ""             8002 || true
  run_arm "triton_tp${TP}"   "$TP" 0 "TRITON_ATTN"  8003 || true
  run_arm "bitriton_tp${TP}" "$TP" 1 "TRITON_ATTN"  8004 || true
done
echo "E_A_FULL_DONE $(date -u)"
sha256sum "$OUT"/eA_*_$J.summary.json "$OUT"/eA_*_$J.jsonl > "$OUT/eA_SHA256SUMS_$J.txt" 2>/dev/null || true
cat "$OUT/eA_SHA256SUMS_$J.txt" || true
