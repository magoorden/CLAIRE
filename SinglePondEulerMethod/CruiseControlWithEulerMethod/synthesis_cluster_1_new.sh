#!/bin/bash
#SBATCH --mail-type=ALL  # Type of email notification: BEGIN,END,FAIL,ALL
#SBATCH --mail-user=mgoorden@cs.aau.dk
#SBATCH --partition=naples  # Which partitions may your job be scheduled on
#SBATCH --mem=300G  # Memory limit that slurm allocates
#SBATCH --time=8:00:00  # (Optional) time limit in dd:hh:mm:ss format. Make sure to keep an eye on your jobs (using 'squeue -u $(whoami)') anyways.

# Memory limit for user program
let "m=1024*1024*300"  
ulimit -v $m

VERIFYTA_DIRECTORY=uppaal-4.1.20-stratego-10-linux64/bin/verifyta
MODEL_PATH=CruiseControlWithEulerMethod/cruise_minmax_corrected_new_method.xml
QUERY_PATH=CruiseControlWithEulerMethod/cruise_minmax_corrected_new_method_new.q
RESULT_PATH=CruiseControlWithEulerMethod/cruise_minmax_corrected_new_method_result_new.txt

CMD="${VERIFYTA_DIRECTORY} -s ${MODEL_PATH} ${QUERY_PATH} >> ${RESULT_PATH}"

eval "${CMD}"
