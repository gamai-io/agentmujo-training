#!/bin/bash
# bal7: dose-response on the "honesty cannot be trained" result.
# Same 800-sample honesty mix as bal6, but 4 epochs instead of 2.
# Question: does more SFT make honesty worse (monotone) or does it plateau?
#SBATCH --job-name=amj_bal7
#SBATCH --account=project_465003647
#SBATCH --partition=small-g
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=7
#SBATCH --gpus-per-node=1
#SBATCH --mem=120G
#SBATCH --time=03:00:00
#SBATCH --output=/project/project_465003647/gama/out/bal7_%j.out
set -uo pipefail
D=/scratch/project_465003647/abtest
SIF=/appl/local/laifs/containers/lumi-multitorch-latest.sif
PYLIBS=/scratch/project_465003647/agentmujo/pylibs
OUTD=/scratch/project_465003647/agentmujo9b/out/run_bal7
EPOCHS=${EPOCHS:-4}
export PYTHONPATH="$PYLIBS"
export SINGULARITYENV_PYTHONPATH="$PYLIBS"
export SINGULARITYENV_HF_HUB_CACHE=/scratch/project_465003647/agentmujo/hfcache
export HF_HUB_CACHE=/scratch/project_465003647/agentmujo/hfcache
export MIOPEN_USER_DB_PATH=/scratch/$USER/miopen_db
export MIOPEN_CUSTOM_CACHE_DIR=/scratch/$USER/miopen_cache
export MAXLEN=2048
mkdir -p "$D" "$OUTD"
curl -fsSL --retry 5 -o "$D/train_bal.py" https://huggingface.co/datasets/renatoschust/amj-dpo-scratch/resolve/main/transfer/train_bal.py || exit 3
[ -s "$D/bal6_data.jsonl" ] || curl -fsSL --retry 5 -o "$D/bal6_data.jsonl" https://huggingface.co/datasets/renatoschust/amj-dpo-scratch/resolve/main/transfer/bal6_data.jsonl || exit 3
echo "DATA_LINES $(wc -l < "$D/bal6_data.jsonl") EPOCHS $EPOCHS"
srun --unbuffered singularity exec -B /pfs:/pfs -B /project:/project -B /scratch:/scratch "$SIF" \
  python3 -u "$D/train_bal.py" none "$D/bal6_data.jsonl" "$OUTD/adapter" "$EPOCHS" 1e-5 || { echo TRAIN_FAILED; exit 4; }
du -sh "$OUTD/adapter" | tee "$OUTD/adapter_size.txt"
cp "$OUTD/adapter_size.txt" /project/project_465003647/gama/out/bal7_adapter_size_$SLURM_JOB_ID.txt 2>/dev/null || true
echo BAL7_DONE
