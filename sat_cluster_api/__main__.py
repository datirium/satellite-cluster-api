"""
The satellite cluster api expects 2 arguments when run
1: the directory (relative to user home_dir) where job/cwl files should be stored
    (default = 'tmp_job_dir') 
2: the directory (relative to user home_dir) where the run_toil script can be found
    (default = 'scripts')
"""

import connexion
import urllib
import os
import json
import yaml
from datetime import datetime
import base64
import gzip
from ruamel.yaml import YAML
import sys

# app = connexion.FlaskApp(__name__)

# home_directory = os.path.expanduser( '~' )
cli_args = sys.argv
# for i, arg in enumerate(cli_args):
#     print(f'Arg #{i}: {arg}')
job_dir = cli_args[1] if len(cli_args) > 1 else 'tmp_job_dir'
script_dir = cli_args[2] if len(cli_args) > 2 else 'scripts'
tmp_output_dir = cli_args[3] if len(cli_args) > 3 else '/data/barskilab/scidap_data'


app = connexion.FlaskApp(
    __name__
    # 'localhost', # host=args.host,
    # port=args.port,
    # specification_dir="openapi",
    # server="tornado"
)


def post_greeting(name: str):
    return f"Hello {name}", 200

def test_get():
    return f'some message', 200

def test_post(cwlLocation: str):
    return f'given str: {cwlLocation}', 200

def post_dags_dag_runs(
    dag_id: str, run_id: str, 
    conf: str, workflow_content: str,
): 
    """
    TODO: 
        - post dag (save to DB if needed)
        - clean up dag runs (stop currently running one since getting this means sample was restarted)
        - start cwlToil based on config and workflow_content
    """
    # dir_path = f'{home_directory}/{job_dir}' 
    # print(f'dirname: {dir_path}')

    ### save job file
    conf_dict = json.loads(conf)
    output_folder = conf_dict['job']['outputs_folder']
    # remove outputs_folder from job
    del conf_dict['job']['outputs_folder']
    # print(f'config dict: {conf_dict}')
    # print(f'outptus folder: {output_folder}')
    job_filename = f'{job_dir}/{run_id}/job.yml'
    # print(f'file name: {job_filename}')
    os.makedirs(os.path.dirname(job_filename), exist_ok=True)
    with open(job_filename, 'w') as outfile:
        yaml.dump(conf_dict, outfile, default_flow_style=False)
        # print(f'outfile: {outfile}')


    ### save cwl file
    cwl_filename = f'{job_dir}/{run_id}/workflow.cwl'
    
    # unzip
    uncompressed = gzip.decompress(
        base64.b64decode(
            workflow_content.encode("utf-8") + b'=='       # safety measure to prevent incorrect padding error
        )
    ).decode("utf-8")

    cwl_json = json.loads(uncompressed)
    # print(f'cwl_json: {cwl_json}')

    # save file
    with open(cwl_filename, 'w') as outfile:
        yaml.dump(json.loads(uncompressed), outfile, default_flow_style=False, allow_unicode = True)#, encoding = None)


    ### run toil script with params
    bash_command = f'bash {script_dir}/run_toil.sh {cwl_filename} {job_filename} {output_folder} {tmp_output_dir} {dag_id} {run_id}'
    os.system(f'{bash_command} &')

    start_date_str = datetime.now()
    return {
        'dag_id': dag_id or 'unknown',
        'run_id': run_id or 'unknown',
        'execution_date': start_date_str,
        'start_date': start_date_str,
        'state': 'running'
    }

app.add_api(specification="openapi.yaml")


if __name__ == '__main__':
    # run our standalone gevent server
    app.run(host='127.0.0.1', port=8081)

def run_app():
    app.run(host='127.0.0.1', port=8081)