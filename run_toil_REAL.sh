
#!/bin/bash
set -e

WORKFLOW=$1
JOB=$2
OUTDIR=$3
TMPDIR=$4 # must be accessible by all nodes /data/barskilab/michael/toil_temp
DAG_ID=$5
RUN_ID=$6
TOIL_ENV_FILE=$7
SINGULARITY_TMP_DIR=$8
NJS_CLIENT_PORT=${9:-"3069"}
CWL_SINGULARITY_CACHE=${10:-"${SINGULARITY_TMP_DIR}"}
MEMORY=${11:-"68719476736"}
CPU=${12:-"8"}


# remove file formats from cwl
sed '/\"format\": [/,/]/ d; /^$/d' $WORKFLOW
sed -i '/"format": /d' $WORKFLOW
#fix absolute paths on some input locations
sed -i 's@"location": "file:///scidap@"location": "file:///data/barskilab/scidap_server@g' $JOB

JOBSTORE="${TMPDIR}/${DAG_ID}_${RUN_ID}/jobstore"
LOGS="${TMPDIR}/${DAG_ID}_${RUN_ID}/logs"


cleanup()
{
  EXIT_CODE=$?
  echo "Sending workflow execution error"
  PAYLOAD="{\"payload\":{\"dag_id\": \"${DAG_ID}\", \"run_id\": \"${RUN_ID}\", \"state\": \"failed\", \"progress\": 0, \"error\": \"failed\", \"statistics\": \"\", \"logs\": \"\"}}"
  echo $PAYLOAD
  curl -X POST http://localhost:${NJS_CLIENT_PORT}/airflow/progress -H "Content-Type: application/json" -d "${PAYLOAD}"
  exit ${EXIT_CODE}
}
trap cleanup SIGINT SIGTERM SIGKILL ERR

/cm/shared/apps/lsf10/10.1/linux3.10-glibc2.17-x86_64/bin/bsub -J "${DAG_ID}_${RUN_ID}" \
     -M 64000 \
     -W 48:00 \
     -n 4 \
     -R "rusage[mem=64000] span[hosts=1]" \
     -o "${OUTDIR}/stdout.txt" \
     -e "${OUTDIR}/stderr.txt" << EOL
module purge
module load nodejs anaconda3 singularity/3.7.0
source $TOIL_ENV_FILE
mkdir -p ${OUTDIR} ${LOGS}
rm -rf ${JOBSTORE}
export TMPDIR="${TMPDIR}/${DAG_ID}_${RUN_ID}"
export SINGULARITY_TMPDIR=$SINGULARITY_TMP_DIR
export CWL_SINGULARITY_CACHE=$CWL_SINGULARITY_CACHE
export TOIL_LSF_ARGS="-W 48:00"
toil-cwl-runner \
--logDebug \
--bypass-file-store \
--batchSystem lsf \
--singularity \
--retryCount 0 \
--clean always \
--disableCaching \
--defaultMemory ${MEMORY} \
--defaultCores ${CPU} \
--jobStore "${JOBSTORE}" \
--writeLogs ${LOGS} \
--outdir ${OUTDIR} ${WORKFLOW} ${JOB} > ${OUTDIR}/results.json
EOL


/cm/shared/apps/lsf10/10.1/linux3.10-glibc2.17-x86_64/bin/bwait -w "started(${DAG_ID}_${RUN_ID})"
echo "Sending workflow execution progress"
PAYLOAD="{\"payload\":{\"dag_id\": \"${DAG_ID}\", \"run_id\": \"${RUN_ID}\", \"state\": \"Sent to Cluster\", \"progress\": 8, \"error\": \"\", \"statistics\": \"\", \"logs\": \"\"}}"
echo $PAYLOAD
curl -X POST http://localhost:${NJS_CLIENT_PORT}/airflow/progress -H "Content-Type: application/json" -d "${PAYLOAD}"

/cm/shared/apps/lsf10/10.1/linux3.10-glibc2.17-x86_64/bin/bwait -w "done(${DAG_ID}_${RUN_ID})"      # won't be caught by trap if job finished successfully

RESULTS=`cat ${OUTDIR}/results.json`
PAYLOAD="{\"payload\":{\"dag_id\": \"${DAG_ID}\", \"run_id\": \"${RUN_ID}\", \"results\": $RESULTS}}"
echo "Sending workflow execution results from ${OUTDIR}/results.json"
echo $PAYLOAD
curl -X POST http://localhost:${NJS_CLIENT_PORT}/airflow/results -H "Content-Type: application/json" -d "${PAYLOAD}"

echo "Cleaning temporary directory ${TMPDIR}/${DAG_ID}_${RUN_ID}"
/cm/shared/apps/lsf10/10.1/linux3.10-glibc2.17-x86_64/bin/bsub -J "${DAG_ID}_${RUN_ID}_cleanup" \
     -M 16000 \
     -W 8:00 \
     -n 2 \
     -R "rusage[mem=16000] span[hosts=1]" \
     -o "${OUTDIR}/cleanup_stdout.txt" \
     -e "${OUTDIR}/cleanup_stderr.txt" << EOL
rm -rf "${TMPDIR}/${DAG_ID}_${RUN_ID}"
EOL
/cm/shared/apps/lsf10/10.1/linux3.10-glibc2.17-x86_64/bin/bwait -w "ended(${DAG_ID}_${RUN_ID}_cleanup)"