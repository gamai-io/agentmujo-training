#!/bin/bash
# Merge bal6 LoRA into the multimodal base, then run bench v2 (NO_THINK=1).
#SBATCH --job-name=amj_bal6v2
#SBATCH --account=project_465003647
#SBATCH --partition=dev-g
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=56
#SBATCH --gres=gpu:mi250:4
#SBATCH --time=02:00:00
#SBATCH --output=/project/project_465003647/gama/out/bal6v2_%j.out
set -uo pipefail
D=/scratch/project_465003647/abtest
G=/project/project_465003647/gama
SIF=/appl/local/laifs/containers/lumi-multitorch-latest.sif
PYLIBS=/scratch/project_465003647/agentmujo/pylibs
MERGED=/scratch/project_465003647/agentmujo9b/out/run_bal6/merged
export PYTHONPATH="$PYLIBS"
export SINGULARITYENV_PYTHONPATH="$PYLIBS"
export SINGULARITYENV_HF_HUB_CACHE=/scratch/project_465003647/agentmujo/hfcache
export HF_HUB_CACHE=/scratch/project_465003647/agentmujo/hfcache
export NO_THINK=1
export SINGULARITYENV_NO_THINK=1
export MIOPEN_USER_DB_PATH=/scratch/$USER/miopen_db
export MIOPEN_CUSTOM_CACHE_DIR=/scratch/$USER/miopen_cache

cat > "$D/merge_bal6.py" <<'PY'
import glob
import os
import shutil
import torch
from peft import PeftModel
from transformers import AutoTokenizer

B = "/scratch/project_465003647/agentmujo9b/base_model"
A = "/scratch/project_465003647/agentmujo9b/out/run_bal6/adapter"
M = "/scratch/project_465003647/agentmujo9b/out/run_bal6/merged"
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

if [ ! -f "$MERGED/.merged_ok" ]; then
  srun --unbuffered singularity exec -B /pfs:/pfs -B /project:/project -B /scratch:/scratch "$SIF" \
    python3 -u "$D/merge_bal6.py" || { echo MERGE_FAILED; exit 3; }
fi

srun -n1 --gres=gpu:mi250:4 --cpus-per-task=32 singularity exec \
  -B /pfs:/pfs -B /scratch:/scratch -B /project:/project "$SIF" \
  python -m vllm.entrypoints.openai.api_server \
    --model "$MERGED" --served-model-name bal6 --host 127.0.0.1 --port 8000 \
    --tensor-parallel-size 4 --max-model-len 8192 \
    --max-num-seqs 256 --enable-prefix-caching \
    > "$G/out/vllm_bal6v2_$SLURM_JOB_ID.log" 2>&1 &
for i in $(seq 1 450); do
  curl -sf http://127.0.0.1:8000/v1/models >/dev/null && break
  sleep 2
done
curl -sf http://127.0.0.1:8000/v1/models >/dev/null || { echo VLLM_FAIL; tail -30 "$G/out/vllm_bal6v2_$SLURM_JOB_ID.log"; exit 4; }
echo VLLM_READY

srun --overlap --jobid="$SLURM_JOB_ID" -n1 --cpus-per-task=16 singularity exec \
  -B /pfs:/pfs -B /scratch:/scratch -B /project:/project "$SIF" \
  python3 "$G/bench_v2/run_v2.py" --url http://127.0.0.1:8000 --model bal6 \
    --items "$G/bench_v2/items_v2.jsonl" --n 0 --conc 64 --max-tokens 256 \
    --out "$G/out/v2_bal6_$SLURM_JOB_ID.jsonl" \
    --summary "$G/out/v2_bal6_$SLURM_JOB_ID.summary.json"
echo BAL6V2_DONE
