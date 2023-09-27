#!/bin/bash
WORKFLOW=$1
JOB=$2
OUTDIR=$3

LOGS=${4:-"${OUTDIR}/logs"}
TMPDIR=${5:-"${OUTDIR}/tmp"}
MEMORY=${6:-"17592186044416"}
CPU=${7:-"4"}

source /home/scidap/venv/bin/activate

export TOIL_LSF_ARGS="-q docker"
export TMPDIR="${TMPDIR}"

mkdir -p $OUTDIR
mkdir -p $LOGS
mkdir -p $TMPDIR

toil-cwl-runner \
    --logCritical --disableProgress \
    --batchSystem lsf \
    --retryCount 0 \
    --clean always \
    --disableCaching \
    --defaultMemory $MEMORY \
    --defaultCores $CPU \
    --jobStore $TMPDIR/jobstore/ \
    --writeLogs $LOGS \
    --outdir $OUTDIR \
    $WORKFLOW $JOB