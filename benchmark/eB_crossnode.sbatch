#!/bin/bash
# E-B: same TP=4 replica on TWO nodes; identical greedy requests; BI off/on.
# Prereg: PREREG_E_B_2026-11-11.md
#SBATCH --job-name=amj_eB_cross
#SBATCH --account=project_465003647
#SBATCH --partition=small-g
#SBATCH --nodes=2
#SBATCH --ntasks=2
#SBATCH --cpus-per-task=56
#SBATCH --gres=gpu:mi250:4
#SBATCH --time=01:30:00
#SBATCH --output=/project/project_465003647/gama/out/eB_cross_%j.out
set -uo pipefail
BASE=/project/project_465003647/gama; KIT=$BASE/bench_v2; OUT=$BASE/out
MODEL=${MODEL:-/scratch/project_465003647/models/qwen25-7b}
REPS=${REPS:-3}; MAXTOK=${MAXTOK:-128}; J=$SLURM_JOB_ID; PORT=8001
mkdir -p "$OUT"
module purge >/dev/null 2>&1 || true
module load Local-LAIF lumi-aif-singularity-bindings
SIF=/appl/local/laifs/containers/lumi-multitorch-latest.sif
CACHE=/scratch/project_465003647/vllm_cache
export VLLM_CACHE_ROOT="$CACHE" TRITON_CACHE_DIR="$CACHE/triton"
export SINGULARITYENV_VLLM_CACHE_ROOT="$CACHE" SINGULARITYENV_TRITON_CACHE_DIR="$CACHE/triton"
HOSTS=($(scontrol show hostnames "$SLURM_JOB_NODELIST"))
A=${HOSTS[0]}; B=${HOSTS[1]}
echo "DATE=$(date -u) A=$A B=$B MODEL=$MODEL"
PID_A=""; PID_B=""
serve_pair () {
  local bi=$1
  export VLLM_BATCH_INVARIANT="$bi" SINGULARITYENV_VLLM_BATCH_INVARIANT="$bi"
  srun -w "$A" -N1 -n1 --gres=gpu:mi250:4 --cpus-per-task=32 singularity exec \
    -B /scratch:/scratch -B /project:/project -B /appl/local/laifs:/appl/local/laifs "$SIF" \
    python -m vllm.entrypoints.openai.api_server --model "$MODEL" --served-model-name qwen \
      --host 127.0.0.1 --port "$PORT" --tensor-parallel-size 4 --max-model-len 4096 \
      --max-num-seqs 64 --gpu-memory-utilization 0.90 --trust-remote-code \
      > "$OUT/eB_vllm_${A}_bi${bi}_$J.log" 2>&1 &
  PID_A=$!
  srun -w "$B" -N1 -n1 --gres=gpu:mi250:4 --cpus-per-task=32 singularity exec \
    -B /scratch:/scratch -B /project:/project -B /appl/local/laifs:/appl/local/laifs "$SIF" \
    python -m vllm.entrypoints.openai.api_server --model "$MODEL" --served-model-name qwen \
      --host 127.0.0.1 --port "$PORT" --tensor-parallel-size 4 --max-model-len 4096 \
      --max-num-seqs 64 --gpu-memory-utilization 0.90 --trust-remote-code \
      > "$OUT/eB_vllm_${B}_bi${bi}_$J.log" 2>&1 &
  PID_B=$!
  for i in $(seq 1 360); do
    ra=$(srun -w "$A" --overlap --jobid="$J" -n1 --cpus-per-task=2 curl -sf "http://127.0.0.1:$PORT/v1/models" >/dev/null 2>&1 && echo ok || echo no)
    rb=$(srun -w "$B" --overlap --jobid="$J" -n1 --cpus-per-task=2 curl -sf "http://127.0.0.1:$PORT/v1/models" >/dev/null 2>&1 && echo ok || echo no)
    [ "$ra" = ok ] && [ "$rb" = ok ] && return 0
    sleep 3
  done
  return 1
}
stop_pair () { kill "$PID_A" "$PID_B" 2>/dev/null; wait "$PID_A" "$PID_B" 2>/dev/null; sleep 8; }
run_on () { # host tag batch port ref
  local h=$1 tag=$2 b=$3 p=$4 ref=${5:-}; local extra=""
  [ -n "$ref" ] && extra="--reference $ref"
  srun -w "$h" --overlap --jobid="$J" -n1 --cpus-per-task=8 singularity exec \
    -B /scratch:/scratch -B /project:/project "$SIF" \
    python3 "$KIT/eA_atlas.py" --url "http://127.0.0.1:$p" --model qwen --batch "$b" \
      --reps "$REPS" --max-tokens "$MAXTOK" --tag "$tag" \
      --out "$OUT/eB_${tag}_b${b}_$J.jsonl" --summary "$OUT/eB_${tag}_b${b}_$J.summary.json" $extra
}
for BI in 0 1; do
  if ! serve_pair "$BI"; then echo "PAIR_FAIL bi$BI"; tail -10 "$OUT/eB_vllm_${A}_bi${BI}_$J.log"; tail -10 "$OUT/eB_vllm_${B}_bi${BI}_$J.log"; stop_pair; continue; fi
  echo "PAIR_READY bi$BI $(date -u)"
  run_on "$A" "A_bi${BI}" 1 "$PORT"
  run_on "$B" "B_bi${BI}" 1 "$PORT" "$OUT/eB_A_bi${BI}_b1_$J.jsonl"
  run_on "$A" "A_bi${BI}" 8 "$PORT"
  run_on "$B" "B_bi${BI}" 8 "$PORT" "$OUT/eB_A_bi${BI}_b8_$J.jsonl"
  stop_pair
done
echo "E_B_DONE $(date -u)"
sha256sum "$OUT"/eB_*_$J.summary.json > "$OUT/eB_SHA256SUMS_$J.txt" 2>/dev/null || true
cat "$OUT/eB_SHA256SUMS_$J.txt" || true
