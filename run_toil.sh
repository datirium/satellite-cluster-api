#!/bin/bash
set -e


WORKFLOW=$1
JOB=$2
OUTDIR=$3
TMPDIR=$4 # must be accessible by all nodes /data/barskilab/michael/toil_temp
DAG_ID=$5
RUN_ID=$6


# echo workflow location $WORKFLOW
echo job locatoin $JOB
echo outDir $OUTDIR
echo tmpDir $TMPDIR
echo dagID $DAG_ID
echo runID $RUN_ID


# echo testing becoming user and running ls on tmpdir

# sudo su - kot4or
# ls $TMPDIR

sleep 4
echo output after time
