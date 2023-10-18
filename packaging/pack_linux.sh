#!/usr/bin/env bash

MANYLINUX_VERSION=$1      # This means that downloaded python version has been built in CentOS 7. See https://www.python.org/dev/peps/pep-0599/ for details.
PYTHON_VERSION=$2         # Three digits. Before build check the latest available versions on https://github.com/niess/python-appimage/tags
CLUSTER_VERSION=$3    # Will be always pulled from GitHub. Doesn't support build from local directory

# WORKING_DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
WORKING_DIR=/tmp

echo "Packing cluster-api ($CLUSTER_VERSION) for Python ${PYTHON_VERSION}"
echo "Current working directory ${WORKING_DIR}"

sleep 5

SHORT_PYTHON_VERSION=$(echo ${PYTHON_VERSION} | cut -d "." -f 1,2)
SHORT_PYTHON_VERSION_MONO=$(echo ${PYTHON_VERSION} | cut -d "." -f 1,2 | tr -d ".")

PYTHON_URL="https://github.com/niess/python-appimage/releases/download/python${SHORT_PYTHON_VERSION}/python${PYTHON_VERSION}-cp${SHORT_PYTHON_VERSION_MONO}-cp${SHORT_PYTHON_VERSION_MONO}-manylinux${MANYLINUX_VERSION}_x86_64.AppImage"
PYTHON_APPIMAGE="python${PYTHON_VERSION}-cp${SHORT_PYTHON_VERSION_MONO}-cp${SHORT_PYTHON_VERSION_MONO}-manylinux${MANYLINUX_VERSION}_x86_64.AppImage"
# CLUSTER_API_URL="https://github.com/datirium/satellite-cluster-api"

echo "Installing required dependencies through yum: wget git gcc"
yum install wget git gcc -y

echo "Creating build folder"
mkdir -p $WORKING_DIR/python3
cd $WORKING_DIR/python3

echo "Downloading and extracting Python ${PYTHON_VERSION} with --appimage-extract option"
wget $PYTHON_URL
chmod +x $PYTHON_APPIMAGE
./$PYTHON_APPIMAGE --appimage-extract
mv squashfs-root python${PYTHON_VERSION}
rm $PYTHON_APPIMAGE
# echo "Skipping python extraction step (for now)"

# echo "Cloning Cluster-API"
# # git clone $CLUSTER_API_URL
# mkdir satellite-cluster-api
# mv /tmp/cluster-api ./satellite-cluster-api
# cd satellite-cluster-api
# # echo "Switch to ${CLUSTER_VERSION} branch/tag"
# # git checkout $CLUSTER_VERSION
# echo "ls output: "
# ls
echo "using local copy so no git clone"

echo "going to cluster api dir"
cd /tmp/python3/cluster_api
# echo "ls: "
# echo $(ls)

# sleep 10


echo "Install Cluster-API using dependency constraints from requirements.txt"
# ../python${PYTHON_VERSION}/AppRun -m pip install ".[crypto,postgres]" --constraint ./packaging/constraints/constraints-${SHORT_PYTHON_VERSION}.txt
../python${PYTHON_VERSION}/AppRun -m pip install -r requirements.txt
# ../python${PYTHON_VERSION}/AppRun -m pip install -r pyproject.toml
# cd ..
# rm -rf satellite-cluster-api
cd $WORKING_DIR/python3

echo "Creating bin_portable folder"
mkdir -p ./bin_portable
cd ./python${PYTHON_VERSION}/opt/python${SHORT_PYTHON_VERSION}/bin

TEMPLATE='#!/bin/bash\nBASE_DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )\nexport PATH="$BASE_DIR/python'$PYTHON_VERSION'/usr/bin":"$PATH"\n'

for file in .* *
do
    if [[ -f "$file" ]] && [[ -x "$file" ]]
    then
        echo "Process '$file'"
        echo -e $TEMPLATE > ../../../../bin_portable/$file
        echo "$file \"\$@\"" >> ../../../../bin_portable/$file
    else
        echo "Skip '$file'"
    fi
done
cd ../../../..
chmod +x ./bin_portable/*
cd ..

echo "Updating permissions to u+w for python3 folder"
chmod -R u+w python3

echo "Compressing relocatable Python ${PYTHON_VERSION} with installed cluster-api ($CLUSTER_VERSION) to tar.gz"
#OUTPUT_NAME="python_${PYTHON_VERSION}_cwl_airflow_${CLUSTER_VERSION}_linux.tar.gz"
OUTPUT_NAME="python_${PYTHON_VERSION}_toil_api_master_linux.tar.gz"
tar -zcf $OUTPUT_NAME python3
mv $OUTPUT_NAME python3/cluster_api
# rm -rf python3