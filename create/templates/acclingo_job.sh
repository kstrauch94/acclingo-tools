#!/bin/bash

#SBATCH --output=out.%j
#SBATCH --error=err.%j
#SBATCH --time=0:312600       # walltime
#SBATCH --cpus-per-task=4    # number of processor cores (i.e. tasks)
#SBATCH --partition=long

# Good Idea to stop operation on first error.
set -e

# Load environment modules for your application here.
source /etc/profile.d/modules.sh
module purge
module load anaconda3
source deactivate
source activate acclingo

PATHTOACC={ptoa}

INSTANCESDIR=$1
SEED=$2

python ${{PATHTOACC}}/scripts/acclingo --fn_suffix="*" --instance_dir $INSTANCESDIR --binary clingo --run_obj quality --cutoff 10 --ac_budget 60 --tae_class ${{PATHTOACC}}/acclingo/tae/clasp_opt_tae.py --tae_args "{{\"best_known\": \"/home/kstrauch/TT-opt/acclingo/bestbound/bestboundtest.csv\"}}" --pcs_file ${{PATHTOACC}}/pcs/limited_params.pcs --runsolver ${{PATHTOACC}}/binaries/runsolver --seed $SEED

