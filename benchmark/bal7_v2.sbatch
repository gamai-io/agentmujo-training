#!/bin/bash
# bal7 evaluation: merge the 4-epoch LoRA into the base, serve, then measure
# (a) bench v2 (700 items, 4 blocks) and (b) honesty on 500 real obscure entities.
# Compare with bal6 (2 epochs): if honesty falls further, SFT dose-response is monotone.
#SBATCH --job-name=amj_bal7v2
#SBATCH --account=project_465003647
#SBATCH --partition=dev-g
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=56
#SBATCH --gres=gpu:mi250:4
#SBATCH --time=02:00:00
#SBATCH --output=/project/project_465003647/gama/out/bal7v2_%j.out
set -uo pipefail
D=/scratch/project_465003647/abtest
G=/project/project_465003647/gama
KIT=$G/bench_v2
OUT=$G/out
SIF=/appl/local/laifs/containers/lumi-multitorch-latest.sif
PYLIBS=/scratch/project_465003647/agentmujo/pylibs
RUN=/scratch/project_465003647/agentmujo9b/out/run_bal7
MERGED=$RUN/merged
export PYTHONPATH="$PYLIBS"
export SINGULARITYENV_PYTHONPATH="$PYLIBS"
export SINGULARITYENV_HF_HUB_CACHE=/scratch/project_465003647/agentmujo/hfcache
export HF_HUB_CACHE=/scratch/project_465003647/agentmujo/hfcache
export NO_THINK=1
export SINGULARITYENV_NO_THINK=1
export MIOPEN_USER_DB_PATH=/scratch/$USER/miopen_db
export MIOPEN_CUSTOM_CACHE_DIR=/scratch/$USER/miopen_cache
CACHE_ROOT=${VLLM_CACHE_ROOT:-/scratch/project_465003647/vllm_cache}
export VLLM_CACHE_ROOT="$CACHE_ROOT"
export SINGULARITYENV_VLLM_CACHE_ROOT="$CACHE_ROOT"
export TRITON_CACHE_DIR="$CACHE_ROOT/triton"
export SINGULARITYENV_TRITON_CACHE_DIR="$CACHE_ROOT/triton"
mkdir -p "$CACHE_ROOT/triton" "$OUT"

if [ ! -f "$MERGED/.merged_ok" ]; then
cat > "$D/merge_bal7.py" <<'PY'
import glob
import os
import shutil
import torch
from peft import PeftModel
from transformers import AutoTokenizer

B = "/scratch/project_465003647/agentmujo9b/base_model"
A = "/scratch/project_465003647/agentmujo9b/out/run_bal7/adapter"
M = "/scratch/project_465003647/agentmujo9b/out/run_bal7/merged"
T = M + ".tmp"
try:
    from transformers import AutoModelForImageTextToText as Loader
    MODE = "mm"
except Exception:
    from transformers import AutoModelForCausalLM as Loader
    MODE = "text"
print("LOADER_MODE", MODE, flush=True)
shutil.rmtree(T, ignore_errors=True)
m = Loader.from_pretrained(B, dtype=torch.bfloat16, device_map={"": 0})
m = PeftModel.from_pretrained(m, A)
m = m.merge_and_unload()
m.save_pretrained(T, safe_serialization=True)
for pat in ("chat_template.jinja", "tokenizer*", "*.model", "merges.txt", "vocab.json",
            "preprocessor_config.json", "processor_config.json"):
    for f in glob.glob(os.path.join(B, pat)):
        dst = os.path.join(T, os.path.basename(f))
        if not os.path.exists(dst):
            shutil.copy2(f, dst)
AutoTokenizer.from_pretrained(B).save_pretrained(T)
shutil.rmtree(M, ignore_errors=True)
os.rename(T, M)
open(os.path.join(M, ".merged_ok"), "w").write("1\n")
print("MERGED", M)
PY
  srun --unbuffered singularity exec -B /pfs:/pfs -B /project:/project -B /scratch:/scratch "$SIF" \
    python3 -u "$D/merge_bal7.py" || { echo MERGE_FAILED; exit 3; }
fi

srun -n1 --gres=gpu:mi250:4 --cpus-per-task=32 singularity exec \
  -B /pfs:/pfs -B /scratch:/scratch -B /project:/project "$SIF" \
  python -m vllm.entrypoints.openai.api_server \
    --model "$MERGED" --served-model-name bal7 --host 127.0.0.1 --port 8000 \
    --tensor-parallel-size 4 --max-model-len 8192 --max-num-seqs 256 \
    --gpu-memory-utilization 0.90 \
    > "$OUT/vllm_bal7v2_$SLURM_JOB_ID.log" 2>&1 &
for i in $(seq 1 450); do
  curl -sf http://127.0.0.1:8000/v1/models >/dev/null && break
  sleep 2
done
curl -sf http://127.0.0.1:8000/v1/models >/dev/null || { echo VLLM_FAIL; tail -30 "$OUT/vllm_bal7v2_$SLURM_JOB_ID.log"; exit 4; }
echo VLLM_READY

srun --overlap --jobid="$SLURM_JOB_ID" -n1 --cpus-per-task=16 singularity exec \
  -B /pfs:/pfs -B /scratch:/scratch -B /project:/project "$SIF" \
  python3 "$KIT/run_v2.py" --url http://127.0.0.1:8000 --model bal7 \
    --items "$KIT/items_v2.jsonl" --n 0 --conc 64 --max-tokens 256 \
    --out "$OUT/v2_bal7_$SLURM_JOB_ID.jsonl" --summary "$OUT/v2_bal7_$SLURM_JOB_ID.summary.json"

srun --overlap --jobid="$SLURM_JOB_ID" -n1 --cpus-per-task=16 singularity exec \
  -B /pfs:/pfs -B /scratch:/scratch -B /project:/project "$SIF" \
  python3 "$KIT/run_v2.py" --url http://127.0.0.1:8000 --model bal7 \
    --items "$KIT/items_honesty_real.jsonl" --n 0 --conc 64 --max-tokens 128 \
    --out "$OUT/v2hr_bal7_$SLURM_JOB_ID.jsonl" --summary "$OUT/v2hr_bal7_$SLURM_JOB_ID.summary.json"

srun --overlap --jobid="$SLURM_JOB_ID" -n1 --cpus-per-task=4 singularity exec \
  -B /pfs:/pfs -B /scratch:/scratch -B /project:/project "$SIF" \
  python3 "$KIT/score_honesty_real.py" --items "$KIT/items_honesty_real.jsonl" \
    --results "$OUT/v2hr_bal7_$SLURM_JOB_ID.jsonl" --out "$OUT/honesty_real_bal7_$SLURM_JOB_ID.json"
echo BAL7V2_DONE
