#!/bin/bash
set -e

WORKFLOW=$1
JOB=$2
OUTDIR=$3
TMPDIR=$4 # must be accessible by all nodes /data/barskilab/michael/toil_temp
DAG_ID=$5
RUN_ID=$6
MEMORY=${7:-"17179869184"}
CPU=${8:-"4"}

# remove file formats from cwl
sed -i '/format: /d' $WORKFLOW

JOBSTORE="${TMPDIR}/jobstore"
LOGS="${TMPDIR}/logs/${DAG_ID}_${RUN_ID}"

cleanup()
{
  EXIT_CODE=$?
  echo "Sending workflow execution error"
  PAYLOAD="{\"payload\":{\"dag_id\": \"${DAG_ID}\", \"run_id\": \"${RUN_ID}\", \"state\": \"\", \"state\": \"\", \"progress\": 0, \"error\": \"failed\", \"statistics\": \"\"  }}"
  echo $PAYLOAD
  curl -X POST https://localhost:3069/airflow/progress -H "Content-Type: application/json" -d "${PAYLOAD}"
  exit ${EXIT_CODE}
}
trap cleanup SIGINT SIGTERM SIGKILL ERR

bsub -J "toil-cwl-runner" \
     -M 4000 \
     -W 40:00 \
     -n 4 \
     -R "rusage[mem=4000] span[hosts=1]" \
     -o "${OUTDIR}/stdout.txt" \
     -e "${OUTDIR}/stderr.txt" << EOL
module purge
module load nodejs anaconda3 singularity/3.7.0
source /data/barskilab/temporary/myenv/bin/activate
mkdir -p ${OUTDIR} ${TMPDIR} ${JOBSTORE} ${LOGS}
export TMPDIR="${TMPDIR}"
toil-cwl-runner \
--logCritical \
--batchSystem lsf \
--singularity \
--retryCount 0 \
--clean always \
--disableCaching \
--defaultMemory ${MEMORY} \
--defaultCores ${CPU} \
--jobStore "${JOBSTORE}/${DAG_ID}_${RUN_ID}" \
--writeLogs ${LOGS} \
--outdir ${OUTDIR} ${WORKFLOW} ${JOB} > ${OUTDIR}/results.json
EOL

bwait -w "done(toil-cwl-runner)"      # won't be caught by trap if job finished successfully

RESULTS=`cat ${OUTDIR}/results.json`
PAYLOAD="{\"payload\":{\"dag_id\": \"${DAG_ID}\", \"run_id\": \"${RUN_ID}\", \"results\": $RESULTS}}"
echo "Sending workflow execution results from ${OUTDIR}/results.json"
echo $PAYLOAD
curl -X POST https://localhost:3070/airflow/results -H "Content-Type: application/json" -d "${PAYLOAD}"