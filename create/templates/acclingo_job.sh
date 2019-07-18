#!/bin/bash

#SBATCH --output=out.%j
#SBATCH --error=err.%j
#SBATCH --time80:00:00=       # walltime
#SBATCH --cpus-per-task=2    # number of processor cores (i.e. tasks)
#SBATCH --partition=long

# Good Idea to stop operation on first error.
set -e

# Load environment modules for your application here.
module purge
module load anaconda3
source deactivate
source activate acclingo

PATHTOACC={ptoa}

INSTANCESDIR=$1
SEED=$2


python3 ${{PATHTOACC}}/scripts/acclingo --fn_suffix="*" \
        --instance_dir $INSTANCESDIR \ 
        --binary clingo \
        --run_obj quality --cutoff 300 --ac_budget 180000 \
        --tae_class acclingo/tae/clasp_opt_tae.py \
        --tae_args "{{\"best_known\": \"/home/kstrauch/TT-opt/acclingo/bestbound/bestboundtest.csv\"}}" \
        --pcs_file path/to/pcs/file.pcs \
        --runsolver ${{PATHTOACC}}/binaries/runsolver \
        --seed $SEED

