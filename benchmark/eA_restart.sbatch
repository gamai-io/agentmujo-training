#!/bin/bash
# E-A restart: within-process vs across-restart reproducibility.
# BI TP1 and TP4 (2 restarts each) + default TP1 control (2 restarts).
#SBATCH --job-name=amj_eA_restart
#SBATCH --account=project_465003647
#SBATCH --partition=dev-g
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=56
#SBATCH --gres=gpu:mi250:4
#SBATCH --time=01:00:00
#SBATCH --output=/project/project_465003647/gama/out/eA_restart_%j.out
set -uo pipefail
BASE=/project/project_465003647/gama; KIT=$BASE/bench_v2; OUT=$BASE/out
MODEL=${MODEL:-/scratch/project_465003647/models/qwen25-7b}
REPS=${REPS:-3}; MAXTOK=${MAXTOK:-128}; J=$SLURM_JOB_ID
mkdir -p "$OUT"
module purge >/dev/null 2>&1 || true
module load Local-LAIF lumi-aif-singularity-bindings
SIF=/appl/local/laifs/containers/lumi-multitorch-latest.sif
CACHE=/scratch/project_465003647/vllm_cache
export VLLM_CACHE_ROOT="$CACHE" TRITON_CACHE_DIR="$CACHE/triton"
export SINGULARITYENV_VLLM_CACHE_ROOT="$CACHE" SINGULARITYENV_TRITON_CACHE_DIR="$CACHE/triton"
echo "HOST=$(hostname) DATE=$(date -u) MODEL=$MODEL"
serve () {
  local tag=$1 tp=$2 bi=$3 port=$4
  export VLLM_BATCH_INVARIANT="$bi" SINGULARITYENV_VLLM_BATCH_INVARIANT="$bi"
  srun -n1 --gres=gpu:mi250:"$tp" --cpus-per-task=32 singularity exec \
    -B /scratch:/scratch -B /project:/project -B /appl/local/laifs:/appl/local/laifs "$SIF" \
    python -m vllm.entrypoints.openai.api_server --model "$MODEL" --served-model-name qwen \
      --host 127.0.0.1 --port "$port" --tensor-parallel-size "$tp" --max-model-len 4096 \
      --max-num-seqs 64 --gpu-memory-utilization 0.90 --trust-remote-code \
      > "$OUT/eA_r_vllm_${tag}_$J.log" 2>&1 &
  SPID=$!
  for i in $(seq 1 360); do curl -sf "http://127.0.0.1:$port/v1/models" >/dev/null && return 0; sleep 2; done
  return 1
}
stop () { kill "$SPID" 2>/dev/null; wait "$SPID" 2>/dev/null; sleep 6; }
runcell () {
  local tag=$1 b=$2 port=$3 ref=${4:-}
  local extra=""; [ -n "$ref" ] && extra="--reference $ref"
  srun --overlap --jobid="$J" -n1 --cpus-per-task=8 singularity exec \
    -B /scratch:/scratch -B /project:/project "$SIF" \
    python3 "$KIT/eA_atlas.py" --url "http://127.0.0.1:$port" --model qwen --batch "$b" \
      --reps "$REPS" --max-tokens "$MAXTOK" --tag "$tag" \
      --out "$OUT/eA_r_${tag}_b${b}_$J.jsonl" --summary "$OUT/eA_r_${tag}_b${b}_$J.summary.json" $extra
}
arm () { # name tp bi port
  local n=$1 tp=$2 bi=$3 p=$4
  if ! serve "${n}_run1" "$tp" "$bi" "$p"; then echo "ARM_FAIL $n run1"; return 1; fi
  runcell "${n}_run1" 1 "$p"
  stop
  if ! serve "${n}_run2" "$tp" "$bi" "$p"; then echo "ARM_FAIL $n run2"; return 1; fi
  runcell "${n}_run2" 1 "$p" "$OUT/eA_r_${n}_run1_b1_$J.jsonl"
  stop
}
arm bi_tp1 1 1 8011
arm bi_tp4 4 1 8012
arm def_tp1 1 0 8013
echo "E_A_RESTART_DONE $(date -u)"
sha256sum "$OUT"/eA_r_*_$J.json "$OUT"/eA_r_*_$J.jsonl > "$OUT/eA_r_SHA256SUMS_$J.txt" 2>/dev/null || true
cat "$OUT/eA_r_SHA256SUMS_$J.txt" || true
