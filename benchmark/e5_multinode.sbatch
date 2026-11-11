#!/bin/bash
# Multi-node data-parallel scaling: one vLLM replica per node (TP=8), N nodes.
# Submit with: sbatch --nodes=2 benchmark/e5_multinode.sbatch
#SBATCH --job-name=amj_mnode
#SBATCH --account=project_465003647
#SBATCH --partition=dev-g
#SBATCH --nodes=2
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=56
#SBATCH --gres=gpu:mi250:8
#SBATCH --time=01:30:00
#SBATCH --output=/project/project_465003647/gama/out/mnode_%j.out
set -uo pipefail
BASE=/project/project_465003647/gama
KIT=$BASE/bench_v2
OUT=$BASE/out
MODEL=${MODEL:-/scratch/project_465003647/models/mistral-7b-instruct-v0.3}
TAG=${TAG:-mistral}
PARAMS_B=${PARAMS_B:-7.2}
N=${N:-512}
CONCS=${CONCS:-"64 256"}
MAXTOK=${MAXTOK:-128}
PROMPT_TOK=${PROMPT_TOK:-256}
TP=${TP:-8}
PORT=${PORT:-8000}
mkdir -p "$OUT"
module purge >/dev/null 2>&1 || true
module load Local-LAIF lumi-aif-singularity-bindings
SIF=/appl/local/laifs/containers/lumi-multitorch-latest.sif

HOSTS=$(scontrol show hostnames "$SLURM_JOB_NODELIST")
NNODES=$(echo "$HOSTS" | wc -l)
GPUS=$(( NNODES * TP ))
echo "JOB=$SLURM_JOB_ID NODES=$NNODES HOSTS=$(echo $HOSTS) TP=$TP GPUS=$GPUS DATE=$(date -u)"
rocm-smi 2>/dev/null | head -3 || true

for h in $HOSTS; do
  echo "starting server on $h"
  srun --nodes=1 --ntasks=1 --gres=gpu:mi250:"$TP" --cpus-per-task=32 -w "$h" \
    singularity exec -B /scratch:/scratch -B /project:/project \
      -B /appl/local/laifs:/appl/local/laifs "$SIF" \
    python -m vllm.entrypoints.openai.api_server \
      --model "$MODEL" --served-model-name "$TAG" --host 0.0.0.0 --port "$PORT" \
      --tensor-parallel-size "$TP" --max-model-len 8192 --max-num-seqs 256 \
      --gpu-memory-utilization 0.90 --trust-remote-code \
      > "$OUT/vllm_mn_${h}_$SLURM_JOB_ID.log" 2>&1 &
done

READY=1
for h in $HOSTS; do
  ok=0
  for i in $(seq 1 420); do
    if curl -sf "http://$h:$PORT/v1/models" >/dev/null; then ok=1; break; fi
    sleep 2
  done
  echo "ready $h = $ok"
  [ "$ok" = 1 ] || READY=0
done
if [ "$READY" != 1 ]; then echo "SERVER_FAIL"; exit 4; fi

URLS=""
for h in $HOSTS; do
  if [ -z "$URLS" ]; then URLS="http://$h:$PORT"; else URLS="$URLS,http://$h:$PORT"; fi
done
echo "URLS=$URLS"

for C in $CONCS; do
  srun --overlap --jobid="$SLURM_JOB_ID" --nodes=1 --ntasks=1 --cpus-per-task=16 \
    -w "$(echo "$HOSTS" | head -1)" \
    singularity exec -B /scratch:/scratch -B /project:/project "$SIF" \
    python3 "$KIT/loadgen.py" --url "$URLS" --model "$TAG" \
      --n "$N" --conc "$C" --max-tokens "$MAXTOK" --prompt-tokens "$PROMPT_TOK" \
      --gpus "$GPUS" --params-b "$PARAMS_B" \
      --out "$OUT/mnode_n${NNODES}_c${C}_$SLURM_JOB_ID.json"
  echo "RUN_DONE nodes=$NNODES conc=$C"
done

cat > "$OUT/mnode_agg_$SLURM_JOB_ID.py" <<'PY'
import glob, json, os, sys
out, job = sys.argv[1], sys.argv[2]
rows = []
for p in sorted(glob.glob(os.path.join(out, f"mnode_n*_c*_{job}.json"))):
    d = json.load(open(p))
    rows.append({"nodes": d["gpus"] // 8, "gpus": d["gpus"], "conc": d["conc"],
                 "rps": d["rps"], "tok_s": d["output_tokens_per_s"],
                 "p50": d["latency_s"]["p50"], "p95": d["latency_s"]["p95"],
                 "mfu": d["mfu_estimate"], "errors": d["errors"]})
rows.sort(key=lambda r: (r["conc"], r["nodes"]))
BASE = {64: 31.24, 256: 70.49}   # single-node TP=8, Mistral-7B (job 23625077)
for r in rows:
    b = BASE.get(r["conc"])
    r["speedup_vs_1node"] = round(r["rps"] / b, 2) if b else None
json.dump({"job": job, "rows": rows}, open(os.path.join(out, f"e5_multinode_{job}.json"), "w"), indent=2)
print(f"{'conc':>5s} {'nodes':>5s} {'gpus':>5s} {'rps':>7s} {'tok/s':>8s} {'speedup':>8s} {'MFU':>6s}")
for r in rows:
    print(f"{r['conc']:5d} {r['nodes']:5d} {r['gpus']:5d} {r['rps']:7.1f} {r['tok_s']:8.1f} "
          f"{str(r['speedup_vs_1node']):>8s} {r['mfu']:6.1%}")
PY
srun --overlap --jobid="$SLURM_JOB_ID" --nodes=1 --ntasks=1 --cpus-per-task=4 \
  -w "$(echo "$HOSTS" | head -1)" \
  singularity exec -B /scratch:/scratch -B /project:/project "$SIF" \
  python3 "$OUT/mnode_agg_$SLURM_JOB_ID.py" "$OUT" "$SLURM_JOB_ID"
echo "MNODE_DONE $(date -u)"
