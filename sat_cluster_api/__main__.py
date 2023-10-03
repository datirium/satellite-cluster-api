"""
The satellite cluster api expects 3 arguments when run
1: the directory (absolute_path) where job/cwl files should be stored
    (default = '/home/scidap/tmp_job_dir') 
2: the directory (absolute_path) where the run_toil script can be found
    (default = '/home/scidap/scripts')
3: the directory (absolute_path) where temporary run data is stored
    (default = '/data/barskilab/scidap_data')
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
from cwlformat.formatter import cwl_format, stringify_dict

# home_directory = os.path.expanduser( '~' )
cli_args = sys.argv
# for i, arg in enumerate(cli_args):
#     print(f'Arg #{i}: {arg}')
job_dir = cli_args[1] if len(cli_args) > 1 else '/home/scidap/tmp_job_dir'
script_dir = cli_args[2] if len(cli_args) > 2 else '/home/scidap/scripts'
tmp_output_dir = cli_args[3] if len(cli_args) > 3 else '/data/barskilab/scidap_data'


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
    job_filename = f'{job_dir}/{project_id}/{run_id}/job.yml'
    cwl_filename = f'{job_dir}/{project_id}/{run_id}/workflow.cwl'
    temp_out_dir = f'{tmp_output_dir}/{dag_id}/{run_id}'
    os.makedirs(os.path.dirname(f'{job_dir}/{project_id}/{run_id}/'), exist_ok=True)
    # os.makedirs(os.path.dirname(f'{temp_out_dir}/'), exist_ok=True)

    ### save job file
    # print(f'file name: {job_filename}')
    with open(job_filename, 'w') as outfile:
        yaml.dump(conf_dict['job'], outfile, default_flow_style=False)


    ### save cwl file
    # unzip
    uncompressed = gzip.decompress(
        base64.b64decode(
            workflow_content.encode("utf-8") + b'=='       # safety measure to prevent incorrect padding error
        )
    ).decode("utf-8")
    cwl_json = json.loads(uncompressed)
    # save file
    ## json loading causes issues with full width dollar sign
    # with open(cwl_filename, 'w') as outfile:
        # loaded_cwl = json.loads(uncompressed)
        # print(f'type of loaded cwl: {type(loaded_cwl)}')
        # yaml.dump(loaded_cwl, outfile, default_flow_style=False)#, allow_unicode = True)#, encoding = None)

    ## yaml loading doesn't fix dollar sign issue
    # with open(cwl_filename, 'w') as outfile:
    #     yaml_obj = YAML(typ="safe")
    #     cwl_yaml = yaml_obj.load(uncompressed)
    #     print(f'cwl yaml: \n{cwl_yaml}')
    #     # yaml_obj.preserve_quotes = True
    #     yaml.default_flow_style = False
    #     # yaml_obj.indent(mapping=4, sequence=6, offset=3)
    #     # yaml_obj.compact(seq_seq=False, seq_map=False)
    #     yaml_obj.dump(cwl_yaml, outfile)



    formatted_cwl_str = stringify_dict(cwl_json)
    formatted_cwl_str = formatted_cwl_str.replace('＄', '$')
    # print(f'stringifed cwl: \n{formatted_cwl_str}')
    with open(cwl_filename, 'w') as outfile:
        outfile.write(formatted_cwl_str)

    # # trying to replace full width dollar sign explicitly doesnt work right
    # with open(cwl_filename, 'r') as file:
    #     cwl_str_data = file.read()
    #     cwl_str_data = cwl_str_data.replace('＄', '$') #'\\uFF04', '$')


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


# if __name__ == '__main__':
#     # run our standalone gevent server
#     app.run(host='127.0.0.1', port=8081)

def run_app():
    app.run(host='127.0.0.1', port=8081)