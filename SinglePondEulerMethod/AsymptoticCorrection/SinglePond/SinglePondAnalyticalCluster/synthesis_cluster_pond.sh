#!/bin/bash
#SBATCH --mail-type=ALL  # Type of email notification: BEGIN,END,FAIL,ALL
#SBATCH --mail-user=mgoorden@cs.aau.dk
#SBATCH --partition=naples  # Which partitions may your job be scheduled on
#SBATCH --mem=200G  # Memory limit that slurm allocates
#SBATCH --time=4:00:00  # (Optional) time limit in dd:hh:mm:ss format. Make sure to keep an eye on your jobs (using 'squeue -u $(whoami)') anyways.

# Memory limit for user program
let "m=1024*1024*200"  
ulimit -v $m

VERIFYTA_DIRECTORY=uppaal-5.0.0-rc5-linux64/bin/verifyta.sh
MODEL_PATH=SinglePondAnalyticalCluster/pond_scaled_analytic_asymptotic_equilibrium.xml
QUERY_PATH=SinglePondAnalyticalCluster/pond_scaled.q
RESULT_PATH=SinglePondAnalyticalCluster/pond_scaled_analytic_asymptotic_equilibrium_result.txt

CMD="${VERIFYTA_DIRECTORY} -s ${MODEL_PATH} ${QUERY_PATH} >> ${RESULT_PATH}"

eval "${CMD}"
