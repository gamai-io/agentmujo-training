#!/bin/bash
# Intra-node scaling + MFU: one full LUMI-G node (8 GCDs), TP = 1/2/4/8.
# Fixed workload: 512 requests, 256 prompt tokens, 128 generated tokens (ignore_eos).
#SBATCH --job-name=amj_scaling
#SBATCH --account=project_465003647
#SBATCH --partition=dev-g
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=56
#SBATCH --gres=gpu:mi250:8
#SBATCH --time=02:00:00
#SBATCH --output=/project/project_465003647/gama/out/scaling_%j.out
set -uo pipefail
BASE=/project/project_465003647/gama
KIT=$BASE/bench_v2
OUT=$BASE/out
MODEL=${MODEL:-/scratch/project_465003647/models/qwen25-7b}
PORT=${PORT:-8000}
N=${N:-512}
CONCS=${CONCS:-"64 256"}
TPS=${TPS:-"1 2 4 8"}
PARAMS_B=${PARAMS_B:-7.6}
MAXTOK=${MAXTOK:-128}
PROMPT_TOK=${PROMPT_TOK:-256}
mkdir -p "$OUT"
module purge >/dev/null 2>&1 || true
module load Local-LAIF lumi-aif-singularity-bindings
SIF=/appl/local/laifs/containers/lumi-multitorch-latest.sif

echo "HOST=$(hostname) DATE=$(date -u) MODEL=$MODEL N=$N CONCS=$CONCS TPS=$TPS"
rocm-smi 2>/dev/null | head -4 || true

for TP in $TPS; do
  echo "=== TP=$TP $(date -u)"
  srun -n1 --gres=gpu:mi250:"$TP" --cpus-per-task=32 singularity exec \
    -B /scratch:/scratch -B /project:/project -B /appl/local/laifs:/appl/local/laifs "$SIF" \
    python -m vllm.entrypoints.openai.api_server \
      --model "$MODEL" --served-model-name qwen --host 127.0.0.1 --port "$PORT" \
      --tensor-parallel-size "$TP" --max-model-len 8192 --max-num-seqs 256 \
      --gpu-memory-utilization 0.90 --trust-remote-code \
      > "$OUT/vllm_scal_tp${TP}_$SLURM_JOB_ID.log" 2>&1 &
  SPID=$!
  ok=0
  for i in $(seq 1 420); do
    if curl -sf "http://127.0.0.1:$PORT/v1/models" >/dev/null; then ok=1; break; fi
    sleep 2
  done
  if [ "$ok" != 1 ]; then
    echo "VLLM_FAIL TP=$TP"; tail -20 "$OUT/vllm_scal_tp${TP}_$SLURM_JOB_ID.log"
    kill "$SPID" 2>/dev/null; continue
  fi
  echo "VLLM_READY TP=$TP $(date -u)"
  for C in $CONCS; do
    srun --overlap --jobid="$SLURM_JOB_ID" -n1 --cpus-per-task=16 singularity exec \
      -B /scratch:/scratch -B /project:/project "$SIF" \
      python3 "$KIT/loadgen.py" --url "http://127.0.0.1:$PORT" --model qwen \
        --n "$N" --conc "$C" --max-tokens "$MAXTOK" --prompt-tokens "$PROMPT_TOK" \
        --gpus "$TP" --params-b "$PARAMS_B" \
        --out "$OUT/scal_tp${TP}_c${C}_$SLURM_JOB_ID.json"
    echo "RUN_DONE tp=$TP conc=$C"
  done
  kill "$SPID" 2>/dev/null; wait "$SPID" 2>/dev/null; sleep 5
done

cat > "$OUT/scal_agg_$SLURM_JOB_ID.py" <<'PY'
import glob, json, os, sys
out, job = sys.argv[1], sys.argv[2]
rows = []
for p in sorted(glob.glob(os.path.join(out, f"scal_tp*_c*_{job}.json"))):
    d = json.load(open(p))
    rows.append({"tp": d["gpus"], "conc": d["conc"], "rps": d["rps"],
                 "out_tokens_per_s": d["output_tokens_per_s"],
                 "lat_p50": d["latency_s"]["p50"], "lat_p95": d["latency_s"]["p95"],
                 "mfu": d["mfu_estimate"], "errors": d["errors"]})
rows.sort(key=lambda r: (r["conc"], r["tp"]))
res = {"job": job, "rows": rows}
json.dump(res, open(os.path.join(out, f"e5_scaling_{job}.json"), "w"), indent=2)
print(f"{'conc':>5s} {'tp':>3s} {'rps':>7s} {'tok/s':>8s} {'p50':>6s} {'p95':>6s} {'MFU':>6s}")
for r in rows:
    print(f"{r['conc']:5d} {r['tp']:3d} {r['rps']:7.1f} {r['out_tokens_per_s']:8.1f} "
          f"{r['lat_p50']:6.2f} {r['lat_p95']:6.2f} {r['mfu']:6.1%}")
PY
srun --overlap --jobid="$SLURM_JOB_ID" -n1 --cpus-per-task=4 singularity exec \
  -B /scratch:/scratch -B /project:/project "$SIF" \
  python3 "$OUT/scal_agg_$SLURM_JOB_ID.py" "$OUT" "$SLURM_JOB_ID"
echo "SCALING_DONE $(date -u)"
