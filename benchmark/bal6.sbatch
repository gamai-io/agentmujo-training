#!/bin/bash
#SBATCH --job-name=amj_bal6
#SBATCH --account=project_465003647
#SBATCH --partition=small-g
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=7
#SBATCH --gpus-per-node=1
#SBATCH --mem=120G
#SBATCH --time=03:00:00
#SBATCH --output=/project/project_465003647/gama/out/bal6_%j.out
set -uo pipefail
D=/scratch/project_465003647/abtest
SIF=/appl/local/laifs/containers/lumi-multitorch-latest.sif
PYLIBS=/scratch/project_465003647/agentmujo/pylibs
OUTD=/scratch/project_465003647/agentmujo9b/out/run_bal6
export PYTHONPATH="$PYLIBS"
export SINGULARITYENV_PYTHONPATH="$PYLIBS"
export SINGULARITYENV_HF_HUB_CACHE=/scratch/project_465003647/agentmujo/hfcache
export HF_HUB_CACHE=/scratch/project_465003647/agentmujo/hfcache
export MIOPEN_USER_DB_PATH=/scratch/$USER/miopen_db
export MIOPEN_CUSTOM_CACHE_DIR=/scratch/$USER/miopen_cache
export MAXLEN=2048
curl -fsSL --retry 5 -o "$D/train_bal.py" https://huggingface.co/datasets/renatoschust/amj-dpo-scratch/resolve/main/transfer/train_bal.py || exit 3
curl -fsSL --retry 5 -o "$D/bal6_data.jsonl" https://huggingface.co/datasets/renatoschust/amj-dpo-scratch/resolve/main/transfer/bal6_data.jsonl || exit 3
mkdir -p "$OUTD"
srun --unbuffered singularity exec -B /pfs:/pfs -B /project:/project -B /scratch:/scratch "$SIF" \
  python3 -u "$D/train_bal.py" none "$D/bal6_data.jsonl" "$OUTD/adapter" 2 1e-5 || { echo TRAIN_FAILED; exit 4; }
srun --unbuffered singularity exec -B /pfs:/pfs -B /project:/project -B /scratch:/scratch "$SIF" \
  python3 -u "$D/eval_multi2.py" "$OUTD/adapter" bal6 "$D/tf_multi2.jsonl" || { echo EVAL_FAILED; exit 5; }
echo BAL6_DONE
