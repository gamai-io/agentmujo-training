#!/bin/bash
# Cross-family replication of bench v2 on LUMI (MI250X, 4 GCD).
# Two non-Qwen families, 3 seeds each, same 700 items. Also reports seed-to-seed
# stability (how many items flip), which is the honest substitute for bit-identity.
#SBATCH --job-name=amj_crossfam
#SBATCH --account=project_465003647
#SBATCH --partition=small-g
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=56
#SBATCH --gres=gpu:mi250:4
#SBATCH --time=02:30:00
#SBATCH --output=/project/project_465003647/gama/out/crossfam_%j.out
set -uo pipefail
BASE=/project/project_465003647/gama
KIT=$BASE/bench_v2
OUT=$BASE/out
MODELS_DIR=/scratch/project_465003647/models
ITEMS=${ITEMS:-$KIT/items_v2.jsonl}
TP=${TP:-4}
PORT=${PORT:-8000}
MAXTOK=${MAXTOK:-256}
SEEDS=${SEEDS:-42 43 44}
MODELS=${MODELS:-"mistral-7b-instruct-v0.3:mistral phi35-mini-instruct:phi35"}
MODEL_PATH=${MODEL_PATH:-}
MODEL_TAG=${MODEL_TAG:-}
if [ -n "$MODEL_PATH" ] && [ -n "$MODEL_TAG" ]; then MODELS="$MODEL_PATH:$MODEL_TAG"; fi
NO_THINK=${NO_THINK:-1}
export NO_THINK
export SINGULARITYENV_NO_THINK="$NO_THINK"
mkdir -p "$OUT"
module purge >/dev/null 2>&1 || true
module load Local-LAIF lumi-aif-singularity-bindings
SIF=/appl/local/laifs/containers/lumi-multitorch-latest.sif

echo "HOST=$(hostname) DATE=$(date -u) TP=$TP SEEDS=$SEEDS NO_THINK=$NO_THINK MODELS=$MODELS"
rocm-smi 2>/dev/null | head -6 || true

serve_model () {
  local path=$1 tag=$2
  srun -n1 --gres=gpu:mi250:"$TP" --cpus-per-task=32 singularity exec \
    -B /scratch:/scratch -B /project:/project -B /appl/local/laifs:/appl/local/laifs "$SIF" \
    python -m vllm.entrypoints.openai.api_server \
      --model "$path" --served-model-name "$tag" --host 127.0.0.1 --port "$PORT" \
      --tensor-parallel-size "$TP" --max-model-len 8192 --max-num-seqs 128 \
      --gpu-memory-utilization 0.90 --trust-remote-code \
      > "$OUT/vllm_cf_${tag}_$SLURM_JOB_ID.log" 2>&1 &
  SERVER_PID=$!
  for i in $(seq 1 360); do
    curl -sf "http://127.0.0.1:$PORT/v1/models" >/dev/null && return 0
    sleep 2
  done
  return 1
}

for spec in $MODELS; do
  M="${spec%%:*}"; TAG="${spec##*:}"
  MPATH="$MODELS_DIR/$M"
  case "$M" in /*) MPATH="$M" ;; esac
  if [ ! -d "$MPATH" ]; then echo "MISSING_MODEL $MPATH"; continue; fi
  echo "=== MODEL $TAG ($MPATH) $(date -u)"
  if ! serve_model "$MPATH" "$TAG"; then
    echo "VLLM_FAIL $TAG"; tail -20 "$OUT/vllm_cf_${TAG}_$SLURM_JOB_ID.log"; continue
  fi
  echo "VLLM_READY $TAG $(date -u)"
  for S in $SEEDS; do
    srun --overlap --jobid="$SLURM_JOB_ID" -n1 --cpus-per-task=16 singularity exec \
      -B /scratch:/scratch -B /project:/project "$SIF" \
      python3 "$KIT/run_v2.py" --url "http://127.0.0.1:$PORT" --model "$TAG" \
        --items "$ITEMS" --n 0 --conc 64 --max-tokens "$MAXTOK" \
        --out "$OUT/v2cf_${TAG}_s${S}_$SLURM_JOB_ID.jsonl" \
        --summary "$OUT/v2cf_${TAG}_s${S}_$SLURM_JOB_ID.summary.json"
    echo "RUN_DONE $TAG seed=$S rc=$?"
  done
  kill "$SERVER_PID" 2>/dev/null
  wait "$SERVER_PID" 2>/dev/null
  sleep 5
done

cat > "$OUT/cf_compare_$SLURM_JOB_ID.py" <<'PY'
import json, os, sys
out_dir, job = sys.argv[1], sys.argv[2]
tags = sys.argv[3].split(",")
seeds = [42, 43, 44]
res = {"job": job, "seeds": seeds, "models": {}}
for tag in tags:
    runs = {}
    for s in seeds:
        p = os.path.join(out_dir, f"v2cf_{tag}_s{s}_{job}.jsonl")
        if os.path.exists(p):
            runs[s] = {r["id"]: r for r in (json.loads(l) for l in open(p, encoding="utf-8") if l.strip())}
    if not runs:
        continue
    base = runs.get(42, {})
    flips = {}
    for s, rows in runs.items():
        if s == 42:
            continue
        diff = sum(1 for i in base if i in rows and bool(base[i]["ok"]) != bool(rows[i]["ok"]))
        flips[s] = diff
    blocks = {}
    for s, rows in runs.items():
        for r in rows.values():
            b = blocks.setdefault(r["block"], {}).setdefault(s, [0, 0])
            b[0] += int(bool(r["ok"])); b[1] += 1
    summ = {}
    for b, per in sorted(blocks.items()):
        summ[b] = {str(s): round(v[0] / v[1], 4) for s, v in sorted(per.items())}
    tot = {}
    for s, rows in runs.items():
        ok = sum(1 for r in rows.values() if r.get("ok"))
        tot[str(s)] = {"ok": ok, "n": len(rows), "acc": round(ok / len(rows), 4)}
    res["models"][tag] = {"per_seed_total": tot, "per_block_acc": summ,
                          "item_flips_vs_seed42": flips}
json.dump(res, open(os.path.join(out_dir, f"e2_crossfamily_{job}.json"), "w"),
          indent=2, ensure_ascii=False)
print(json.dumps(res, indent=2, ensure_ascii=False))
PY

TAGS=$(echo "$MODELS" | sed 's/[^ ]*:\([^ ]*\)/\1/g' | tr ' ' ',')
srun --overlap --jobid="$SLURM_JOB_ID" -n1 --cpus-per-task=4 singularity exec \
  -B /scratch:/scratch -B /project:/project "$SIF" \
  python3 "$OUT/cf_compare_$SLURM_JOB_ID.py" "$OUT" "$SLURM_JOB_ID" "$TAGS"
echo "CROSSFAM_DONE $(date -u)"
