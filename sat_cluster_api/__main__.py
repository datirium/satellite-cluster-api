"""
The satellite cluster api expects 7 arguments when run
$NJS_CLIENT_PORT $SINGULARITY_TMP_DIR $CWL_SINGULARITY_DIR

    1 (OUTPUT_DIR): Directory (absolute_path) where job/cwl files should be stored (will have folders for dag/run ID appended for each POST)
        (default = '/home/scidap/scidap/projects') 
    2 (SCRIPT_DIR): Directory (absolute_path) where the run_toil script can be found
        (default = '/home/scidap/satellite/satellite/bin')
    3 (TMP_TOIL_DIR): Directory (absolute_path) where temporary run data is stored
        (default = '/mnt/cache/TOIL_TMP_DIR')
    4 (ENV_FILE_PATH): File (absolute path) to the python virtual env file sourced by the run_toil script
        (default = '/data/barskilab/temporary/myenv/bin/activate')
    5 (BATCH_SYSTEM): String (either 'lsf' or 'single_machine'). indicates if toil is run in cluster or single machine
        (default = 'single_machine'
    6 (NJS_CLIENT_PORT): Port for njs-client
        (default = 3069)
    7 (SINGULARITY_TMP_DIR): Directory (absolute path) for singularity to use for tmp files (should be shared among all cluster nodes)
        (default = '/mnt/cache/SINGULATIRY_TMP_DIR')
        (OPTIONAL if batch_system=single_machine)
    8 (CWL_SINGULARITY_DIR): Directory (absolute path) for singularity to use for cwls (should be shared among all cluster nodes)
        (default = '/mnt/cache/SINGULARITY_TMP_DIR')
        (OPTIONAL if batch_system=single_machine)
    9 (SYSTEM_ROOT): where satellite is installed at, and where the "projects" folder (that holds all data) is held
    10 (CPUS): number of cpus to utilize???
        (default = 8)
    11 (MAX_MEM): maximum memory given to any individual toil run
        (default = 68719476736)
"""

import connexion
import urllib
import os
import json
from datetime import datetime
import base64
import gzip
import sys
# from cwlformat.formatter import stringify_dict #, cwl_format
# import yaml
from ruamel.yaml import YAML

# home_directory = os.path.expanduser( '~' )
cli_args = sys.argv
num_cli_args = len(cli_args)

job_dir = cli_args[1] if num_cli_args > 1 else '/home/scidap/scidap/projects'
script_dir = cli_args[2] if num_cli_args > 2 else '/home/scidap/satellite/satellite/bin'
tmp_output_dir = cli_args[3] if num_cli_args > 3 else '/mnt/cache/TOIL_TMP_DIR'
# make better default location
toil_env_file = cli_args[4] if num_cli_args > 4 else '/home/scidap/scidap/toilEnvFile'
batch_system = cli_args[5] if num_cli_args > 5 else 'single_machine'
njs_port = cli_args[6] if num_cli_args > 6 else 3069
singularity_tmp_dir = cli_args[7] if num_cli_args > 7 else '/mnt/cache/SINGULARITY_TMP_DIR'
cwl_singularity_dir = cli_args[8] if num_cli_args > 8 else '/mnt/cache/SINGULARITY_TMP_DIR'
system_root = cli_args[9] if num_cli_args > 9 else '/home/scidap/'
num_cpu = cli_args[10] if num_cli_args > 10 else '8'
max_mem = cli_args[11] if num_cli_args > 11 else '68719476736'

app = connexion.FlaskApp(
    __name__
)


def post_greeting(name: str):
    return f"Hello {name}", 200

def test_get():
    return f'some message', 200

def test_post(cwlLocation: str):
    return f'given str: {cwlLocation}', 200

def post_dags_dag_runs(
    # workflow_content: str,
    # workflow_data: str
    body: dict
): 
    """
    TODO: 
        - handle if stopping dag run
        - integrate better progress reporting
    """
    workflow_content = body['workflow_content']
    workflow_data = body['workflow_data']
    ## get data from params
    run_data = workflow_data #json.loads(workflow_data)
    # print(f'run data: {run_data}')
    dag_id = run_data['dag_id']
    run_id = run_data['run_id']
    project_id = run_data['proj_id']
    conf_dict = run_data['conf'] # json.loads(run_data['conf']) # json.loads(conf)
    # print(f'config dict: {conf_dict}')
    output_folder = conf_dict['job']['outputs_folder']
    # remove outputs_folder from job
    del conf_dict['job']['outputs_folder']

    ## configure paths
    job_filename = f'{job_dir}/{project_id}/{run_id}/workflow_job.json'
    cwl_filename = f'{job_dir}/{project_id}/{run_id}/workflow.json'
    temp_out_dir = f'{tmp_output_dir}/{dag_id}/{run_id}'
    os.makedirs(os.path.dirname(f'{job_dir}/{project_id}/{run_id}/'), exist_ok=True)
    # os.makedirs(os.path.dirname(f'{temp_out_dir}/'), exist_ok=True)

    ### save job file
    # print(f'file name: {job_filename}')
    with open(job_filename, 'w') as outfile:
        json.dump(conf_dict['job'], outfile, indent=4) #, default_flow_style=False)


    ### save cwl file
    # unzip

    uncompressed = gzip.decompress(
        base64.b64decode(
            workflow_content.encode("utf-8") + b'=='       # safety measure to prevent incorrect padding error
        )
    ).decode("utf-8")

    # fix issue with full width dollar sign and write workflow to file
    uncompressed = uncompressed.replace('＄', '$')
    yaml = YAML()
    # yaml.preserve_quotes = True
    yaml.indent(mapping=4, sequence=6, offset=3)
    # data = json.loads(uncompressed)
    # print(f'data json loaded steps: \n\n {data["steps"]["extract_fastq"]["run"]["inputs"]["script"]["default"]}')
    data = yaml.load(uncompressed)
    with open(cwl_filename, 'w') as outfile:
        json.dump(data, outfile, indent=4)
        # yaml.dump(data, outfile)


    ### run toil script with params (include data for progress script)
    totalSteps = len(data["steps"].keys())
    bash_command = f'bash {script_dir}/run_toil.sh {cwl_filename} {job_filename} {output_folder} {tmp_output_dir} {dag_id} {run_id} {toil_env_file} {batch_system} {njs_port} {singularity_tmp_dir} {cwl_singularity_dir} {system_root} {num_cpu} {max_mem} {totalSteps} {script_dir}'
    os.system(f'{bash_command} &')
    start_date_str = datetime.now()
    
    # # create cronjob to watch stats until all steps done
    # totalSteps = len(data["steps"].keys())
    # progress_command = f'bash {script_dir}/toil_progress.sh {tmp_output_dir} {dag_id} {run_id} {totalSteps} {njs_port}'
    # os.system(f'{progress_command} &')

    return {
        'dag_id': dag_id or 'unknown',
        'run_id': run_id or 'unknown',
        'execution_date': start_date_str,
        'start_date': start_date_str,
        'state': 'running'
    }

app.add_api(specification="openapi.yaml")

def run_app():
    app.run(host='127.0.0.1', port=8081)