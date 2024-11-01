#!/bin/bash
set -e

# {cwl_filename} {job_filename} {output_folder} {tmp_output_dir} 
WORKFLOW=$1
JOB=$2
OUTDIR=$3
TMPDIR=$4 # must be accessible by all nodes /data/barskilab/michael/toil_temp
# {dag_id} {run_id} {toil_env_file} 
DAG_ID=$5
RUN_ID=$6
TOIL_ENV_FILE=$7
# {batch_system} {njs_port} {singularity_tmp_dir} {cwl_singularity_dir} {num_cpu}
BATCH_SYSTEM=$8
NJS_CLIENT_PORT=${9:-"3069"}
SINGULARITY_TMP_DIR=$10
CWL_SINGULARITY_CACHE=${11:-"${SINGULARITY_TMP_DIR}"}
SYSTEM_ROOT=${12:-"/home/scidap_satellite/scidap"}
CPU=${13:-"6"}
MEMORY=${14:-"68719476736"}
TOTAL_STEPS=${15:-"2"}
SCRIPT_DIR=${16:-"/home/scidap_satellite/satellite/satellite/bin"}

JOBSTORE="${TMPDIR}/${DAG_ID}_${RUN_ID}/jobstore"
LOGS="${TMPDIR}/${DAG_ID}_${RUN_ID}/logs"

    
# # start progress script in background and kill with this
bash $SCRIPT_DIR/toil_progress.sh $TMPDIR $DAG_ID $RUN_ID $TOTAL_STEPS $NJS_CLIENT_PORT &
progressPID=$!

list_descendants ()
{
  local children=$(ps -o pid= --ppid "$1")

  for pid in $children
  do
    list_descendants "$pid"
  done

  echo "$children"
}

cleanup()
{
  EXIT_CODE=$?
  echo "Sending workflow execution error"
  PAYLOAD="{\"payload\":{\"dag_id\": \"${DAG_ID}\", \"run_id\": \"${RUN_ID}\", \"state\": \"failed\", \"progress\": 0, \"error\": \"failed\", \"statistics\": \"\", \"logs\": \"\"}}"
  echo $PAYLOAD
  curl -X POST http://localhost:${NJS_CLIENT_PORT}/airflow/progress -H "Content-Type: application/json" -d "${PAYLOAD}"
  pkill -P $progressPID
  #kill $(list_descendants $$)
  exit ${EXIT_CODE}
}

trap cleanup SIGINT SIGTERM SIGKILL ERR

# remove "format" field from files in cwl
sed -i '/\"format\": \[/,/]/ d; /^$/d' $WORKFLOW
sed -i '/"format": /d' $WORKFLOW


runSingleMode()
{
    trap cleanup SIGINT SIGTERM SIGKILL ERR
    source $TOIL_ENV_FILE
    mkdir -p ${OUTDIR} ${LOGS}
    rm -rf ${JOBSTORE}
    export TMPDIR="${TMPDIR}/${DAG_ID}_${RUN_ID}"
    export SINGULARITY_TMPDIR=$SINGULARITY_TMP_DIR
    export TOIL_LSF_ARGS="-W 48:00"

    echo "Starting workflow execution"
    PAYLOAD="{\"payload\":{\"dag_id\": \"${DAG_ID}\", \"run_id\": \"${RUN_ID}\", \"state\": \"Sent to Cluster\", \"progress\": 8, \"error\": \"\", \"statistics\": \"\", \"logs\": \"\"}}"
    echo $PAYLOAD
    curl -X POST http://localhost:${NJS_CLIENT_PORT}/airflow/progress -H "Content-Type: application/json" -d "${PAYLOAD}"


    toil-cwl-runner \
    --logDebug \
    --stats \
    --bypass-file-store \
    --batchSystem single_machine \
    --retryCount 0 \
    --disableCaching \
    --defaultMemory ${MEMORY} \
    --defaultCores ${CPU} \
    --jobStore "${JOBSTORE}" \
    --writeLogs ${LOGS} \
    --outdir ${OUTDIR} ${WORKFLOW} ${JOB} > ${OUTDIR}/results_full.json
    toil stats ${JOBSTORE} > ${OUTDIR}/stats.txt
    cat ${OUTDIR}/results_full.json | ${SCRIPT_DIR}/jq 'walk(if type == "object" then with_entries(select(.key | test("listing") | not)) else . end)' > ${OUTDIR}/results.json
    
    RESULTS=`cat ${OUTDIR}/results.json`
    PAYLOAD="{\"payload\":{\"dag_id\": \"${DAG_ID}\", \"run_id\": \"${RUN_ID}\", \"results\": $RESULTS}}"
    echo $PAYLOAD > "${OUTDIR}/payload.json"
    echo "Sending workflow execution results from ${OUTDIR}/payload.json"
    curl -X POST http://localhost:${NJS_CLIENT_PORT}/airflow/results -H "Content-Type: application/json" -d @"${OUTDIR}/payload.json"

    echo "Cleaning temporary directory ${TMPDIR}/${DAG_ID}_${RUN_ID}"
    rm -rf "${TMPDIR}"
    pkill -P $progressPID
}

runClusterMode(){
  trap cleanup SIGINT SIGTERM SIGKILL ERR
  
  replacementStr="\"location\": \"file://$SYSTEM_ROOT"
  # echo $replacementStr
  #sed -i "s|\"location\": \"file:///mnt/scidap-storage/PUBLIC_SATELLITE/|$replacementStr|g" $JOB
  sed -i "s|$replacementStr|\"location\": \"file:///mnt/scidap-storage/|g" $JOB
  
  source $TOIL_ENV_FILE
  mkdir -p ${OUTDIR} ${LOGS}
  rm -rf ${JOBSTORE}
  export TMPDIR="${TMPDIR}/${DAG_ID}_${RUN_ID}"
  export SINGULARITY_TMPDIR=$SINGULARITY_TMP_DIR
  export TOIL_LSF_ARGS="-W 48:00"

  echo "Starting workflow execution"
  PAYLOAD="{\"payload\":{\"dag_id\": \"${DAG_ID}\", \"run_id\": \"${RUN_ID}\", \"state\": \"Sent to Cluster\", \"progress\": 8, \"error\": \"\", \"statistics\": \"\", \"logs\": \"\"}}"
  echo $PAYLOAD
  curl -X POST http://localhost:${NJS_CLIENT_PORT}/airflow/progress -H "Content-Type: application/json" -d "${PAYLOAD}"


  toil-cwl-runner \
    --logDebug \
    --stats \
    --bypass-file-store \
    --batchSystem slurm \
    --retryCount 0 \
    --disableCaching \
    --defaultMemory ${MEMORY} \
    --defaultCores ${CPU} \
    --jobStore "${JOBSTORE}" \
    --writeLogs ${LOGS} \
    --outdir ${OUTDIR} ${WORKFLOW} ${JOB} > ${OUTDIR}/results_full.json
    toil stats ${JOBSTORE} > ${OUTDIR}/stats.txt
    cat ${OUTDIR}/results_full.json | ${SCRIPT_DIR}/jq 'walk(if type == "object" then with_entries(select(.key | test("listing") | not)) else . end)' > ${OUTDIR}/results.json
    
    RESULTS=`cat ${OUTDIR}/results.json`
    PAYLOAD="{\"payload\":{\"dag_id\": \"${DAG_ID}\", \"run_id\": \"${RUN_ID}\", \"results\": $RESULTS}}"
    echo $PAYLOAD > "${OUTDIR}/payload.json"
    echo "Sending workflow execution results from ${OUTDIR}/payload.json"
    curl -X POST http://localhost:${NJS_CLIENT_PORT}/airflow/results -H "Content-Type: application/json" -d @"${OUTDIR}/payload.json"

    echo "Cleaning temporary directory ${TMPDIR}/${DAG_ID}_${RUN_ID}"
    rm -rf "${TMPDIR}"
    pkill -P $progressPID

}
if [ "$BATCH_SYSTEM" = "slurm" ]
then
    runClusterMode
elif [ "$BATCH_SYSTEM" = "single_machine" ]
then
    runSingleMode
else 
    echo "BATCH SYSTEM not recognized. job not run"
    cleanup
fi