#!/bin/bash
# E2-determinism: two SERIAL passes (--conc 1, vLLM --max-num-seqs 1) over the same
# 700-item bench v2, then a byte-level comparison of the generated texts.
# Writes $OUT/e2_determinism.json. No model outputs are claimed identical unless proven.
#SBATCH --job-name=amj_e2det
#SBATCH --account=project_465003647
#SBATCH --partition=dev-g
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=56
#SBATCH --gres=gpu:mi250:4
#SBATCH --time=02:00:00
#SBATCH --output=/project/project_465003647/gama/out/e2det_%j.out
set -uo pipefail
BASE=/project/project_465003647/gama
KIT=$BASE/bench_v2
OUT=$BASE/out
MODEL=${MODEL:-/scratch/project_465003647/models/qwen25-7b}
ITEMS=${ITEMS:-$KIT/items_v2.jsonl}
TP=${TP:-4}
PORT=${PORT:-8000}
MAXTOK=${MAXTOK:-256}
MAXSEQS=${MAXSEQS:-1}
OUTJSON=${OUTJSON:-$OUT/e2_determinism.json}
TAG=e2det_$SLURM_JOB_ID
mkdir -p "$OUT"
module purge >/dev/null 2>&1 || true
module load Local-LAIF lumi-aif-singularity-bindings
SIF=/appl/local/laifs/containers/lumi-multitorch-latest.sif

echo "HOST=$(hostname) DATE=$(date -u) MODEL=$MODEL TP=$TP MAXSEQS=$MAXSEQS CONC=1"
rocm-smi 2>/dev/null | head -8 || true

srun -n1 --gres=gpu:mi250:"$TP" --cpus-per-task=32 singularity exec \
  -B /scratch:/scratch -B /project:/project -B /appl/local/laifs:/appl/local/laifs "$SIF" \
  python -m vllm.entrypoints.openai.api_server \
    --model "$MODEL" --host 127.0.0.1 --port "$PORT" \
    --tensor-parallel-size "$TP" --max-model-len 8192 \
    --max-num-seqs "$MAXSEQS" \
    > "$OUT/vllm_$TAG.log" 2>&1 &
for i in $(seq 1 450); do
  curl -sf "http://127.0.0.1:$PORT/v1/models" >/dev/null && break
  sleep 2
done
if ! curl -sf "http://127.0.0.1:$PORT/v1/models" >/dev/null; then
  echo "VLLM_FAIL"; tail -40 "$OUT/vllm_$TAG.log"; exit 2
fi
echo "VLLM_READY $(date -u)"

run_pass () {
  local name=$1
  srun --overlap --jobid="$SLURM_JOB_ID" -n1 --cpus-per-task=16 singularity exec \
    -B /scratch:/scratch -B /project:/project "$SIF" \
    python3 "$KIT/run_v2.py" --url "http://127.0.0.1:$PORT" --model "$MODEL" \
      --items "$ITEMS" --n 0 --conc 1 --max-tokens "$MAXTOK" \
      --out "$OUT/v2_${name}_$SLURM_JOB_ID.jsonl" \
      --summary "$OUT/v2_${name}_$SLURM_JOB_ID.summary.json"
  echo "PASS_${name}_RC=$?"
}

run_pass e2det_a
run_pass e2det_b

A="$OUT/v2_e2det_a_$SLURM_JOB_ID.jsonl"
B="$OUT/v2_e2det_b_$SLURM_JOB_ID.jsonl"
cat > "$OUT/e2_compare_$SLURM_JOB_ID.py" <<'PY'
import hashlib
import json
import os
import sys

a_path, b_path, out_path = sys.argv[1], sys.argv[2], sys.argv[3]
tp, maxseqs = int(sys.argv[4]), int(sys.argv[5])


def load(p):
    rows = []
    with open(p, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


a = load(a_path)
b = load(b_path)
by_b = {r["id"]: r for r in b}
diffs = []
blocks = {}
for r in a:
    o = by_b.get(r["id"], {})
    same = (r.get("text") == o.get("text")) and (r.get("ok") == o.get("ok"))
    blk = blocks.setdefault(r["block"], {"n": 0, "identical": 0, "ok_a": 0, "ok_b": 0})
    blk["n"] += 1
    blk["identical"] += int(same)
    blk["ok_a"] += int(bool(r.get("ok")))
    blk["ok_b"] += int(bool(o.get("ok")))
    if not same:
        diffs.append({"id": r["id"], "block": r["block"],
                      "ok_a": r.get("ok"), "ok_b": o.get("ok"),
                      "text_a": (r.get("text") or "")[:300],
                      "text_b": (o.get("text") or "")[:300]})


def digest(rows):
    h = hashlib.sha256()
    for r in sorted(rows, key=lambda x: x["id"]):
        h.update((r.get("text") or "").encode("utf-8"))
        h.update(b"\x00")
    return h.hexdigest()


n = sum(v["n"] for v in blocks.values())
ident = sum(v["identical"] for v in blocks.values())
res = {
    "e2": "determinism_serial",
    "tp": tp,
    "max_num_seqs": maxseqs,
    "concurrency": 1,
    "a_file": os.path.basename(a_path),
    "b_file": os.path.basename(b_path),
    "n": n,
    "identical": ident,
    "differing": n - ident,
    "identical_rate": round(ident / n, 4) if n else 0.0,
    "sha256_texts_a": digest(a),
    "sha256_texts_b": digest(b),
    "bit_identical": digest(a) == digest(b),
    "blocks": blocks,
    "differences": diffs[:25],
    "verdict": "BIT_IDENTICAL" if ident == n and n > 0 else "NOT_BIT_IDENTICAL",
}
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(res, f, indent=2, ensure_ascii=False)
print(json.dumps({k: res[k] for k in ("n", "identical", "differing", "bit_identical", "verdict")},
                 ensure_ascii=False))
PY

srun --overlap --jobid="$SLURM_JOB_ID" -n1 --cpus-per-task=4 singularity exec \
  -B /scratch:/scratch -B /project:/project "$SIF" \
  python3 "$OUT/e2_compare_$SLURM_JOB_ID.py" "$A" "$B" "$OUTJSON" "$TP" "$MAXSEQS"
echo "E2D_DONE $(date -u)"
