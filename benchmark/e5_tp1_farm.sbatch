#!/bin/bash
# TP=1 replica farm: 8 single-GCD vLLM servers on one node, aggregate throughput.
# Tests the extrapolation from the TP sweep (TP=1 = 32 rps/GCD vs TP=8 = 8.8 rps/GCD).
#SBATCH --job-name=amj_farm
#SBATCH --account=project_465003647
#SBATCH --partition=dev-g
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=56
#SBATCH --gres=gpu:mi250:8
#SBATCH --time=01:30:00
#SBATCH --output=/project/project_465003647/gama/out/farm_%j.out
set -uo pipefail
BASE=/project/project_465003647/gama
KIT=$BASE/bench_v2
OUT=$BASE/out
MODEL=${MODEL:-/scratch/project_465003647/models/mistral-7b-instruct-v0.3}
TAG=${TAG:-mistral}
PARAMS_B=${PARAMS_B:-7.2}
REPLICAS=${REPLICAS:-8}
BASE_PORT=${BASE_PORT:-8000}
N=${N:-2048}
CONCS=${CONCS:-"256 512"}
MAXTOK=${MAXTOK:-128}
PROMPT_TOK=${PROMPT_TOK:-256}
mkdir -p "$OUT"
module purge >/dev/null 2>&1 || true
module load Local-LAIF lumi-aif-singularity-bindings
SIF=/appl/local/laifs/containers/lumi-multitorch-latest.sif
echo "HOST=$(hostname) DATE=$(date -u) REPLICAS=$REPLICAS CONCS=$CONCS"

PIDS=""
for i in $(seq 0 $((REPLICAS-1))); do
  PORT=$((BASE_PORT+i))
  srun -n1 --gres=gpu:mi250:1 --cpus-per-task=6 singularity exec \
    -B /scratch:/scratch -B /project:/project -B /appl/local/laifs:/appl/local/laifs "$SIF" \
    python -m vllm.entrypoints.openai.api_server \
      --model "$MODEL" --served-model-name "$TAG" --host 127.0.0.1 --port "$PORT" \
      --tensor-parallel-size 1 --max-model-len 4096 --max-num-seqs 64 \
      --gpu-memory-utilization 0.85 --trust-remote-code \
      > "$OUT/vllm_farm_${PORT}_$SLURM_JOB_ID.log" 2>&1 &
  PIDS="$PIDS $!"
  sleep 4
done

READY=1
for i in $(seq 0 $((REPLICAS-1))); do
  PORT=$((BASE_PORT+i)); ok=0
  for t in $(seq 1 300); do
    if curl -sf "http://127.0.0.1:$PORT/v1/models" >/dev/null; then ok=1; break; fi
    sleep 2
  done
  echo "ready $PORT=$ok"
  [ "$ok" = 1 ] || READY=0
done
[ "$READY" = 1 ] || { echo FARM_FAIL; exit 4; }

URLS=""
for i in $(seq 0 $((REPLICAS-1))); do
  P=$((BASE_PORT+i))
  if [ -z "$URLS" ]; then URLS="http://127.0.0.1:$P"; else URLS="$URLS,http://127.0.0.1:$P"; fi
done

for C in $CONCS; do
  srun --overlap --jobid="$SLURM_JOB_ID" -n1 --cpus-per-task=16 singularity exec \
    -B /scratch:/scratch -B /project:/project "$SIF" \
    python3 "$KIT/loadgen.py" --url "$URLS" --model "$TAG" --n "$N" --conc "$C" \
      --max-tokens "$MAXTOK" --prompt-tokens "$PROMPT_TOK" --gpus "$REPLICAS" \
      --params-b "$PARAMS_B" --out "$OUT/farm_c${C}_$SLURM_JOB_ID.json"
  echo "RUN_DONE conc=$C"
done
echo "FARM_DONE $(date -u)"
