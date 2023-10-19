"""
The satellite cluster api expects 3 arguments when run
1: the directory (absolute_path) where job/cwl files should be stored
    (default = '/home/scidap/tmp_job_dir') 
2: the directory (absolute_path) where the run_toil script can be found
    (default = '/home/scidap/scripts')
3: the directory (absolute_path) where temporary run data is stored
    (default = '/data/barskilab/scidap_data')
4: the absolute path to the python virtual env file sourced by the run_toil script
    (default = '/data/barskilab/temporary/myenv/bin/activate')
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
job_dir = cli_args[1] if len(cli_args) > 1 else '/home/scidap/scidap/projects'
script_dir = cli_args[2] if len(cli_args) > 2 else '/home/scidap/satellite/satellite/bin'
tmp_output_dir = cli_args[3] if len(cli_args) > 3 else '/mnt/cache/tmp_toil_dir'
# make better default location
toil_env_file = cli_args[4] if len(cli_args) > 4 else '/data/barskilab/temporary/myenv/bin/activate'

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
    job_filename = f'{job_dir}/{project_id}/{run_id}/workflow_job.json'
    cwl_filename = f'{job_dir}/{project_id}/{run_id}/workflow.cwl'
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
    # print(f'uncompressed: {uncompressed}')
    print(f'uncompressed type: {type(uncompressed)}')

    ## (ATTEMPT-2)
    uncompressed = uncompressed.replace('＄', '$')
    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.indent(mapping=4, sequence=6, offset=3)
    # data = yaml.load(uncompressed)
    # if data == uncompressed:
    #     raise ValueError
    data = json.loads(uncompressed)
    print(f'loaded yaml type: {type(data)}')
    with open(cwl_filename, 'w') as outfile:
        yaml.dump(data, outfile)
        # yaml.dump(uncompressed, outfile)

    ## (ATTEMPT-1)
    # yaml = YAML()
    # yaml.preserve_quotes = True
    # data = yaml.load(uncompressed)
    # if data == uncompressed:
    #     raise ValueError
    # print(f'loaded yaml type: {type(data)}')
    # formatted_cwl_str = str(data) 
    # formatted_cwl_str = formatted_cwl_str.replace('＄', '$')
    # print(f'stringified yaml type: {type(formatted_cwl_str)}')
    # with open(cwl_filename, 'w') as outfile:
    #     yaml.dump(formatted_cwl_str, outfile)

    ## (ORIGINAL)
    # cwl_json = json.loads(uncompressed)
    # # print(f'cwl json: {cwl_json}')
    # print(f'type of cwl_json: {type(cwl_json)}')
    # formatted_cwl_str = stringify_dict(cwl_json)
    # formatted_cwl_str = formatted_cwl_str.replace('＄', '$')
    # # print(f'stringifed cwl: \n{formatted_cwl_str}')
    # with open(cwl_filename, 'w') as outfile:
    #     outfile.write(formatted_cwl_str)
    
    ## (ATTEMPT-X) attempting to not use stringify_dict
    # workflow = get_compressed(
    #     convert_to_workflow(                                # to make sure we are not saving CommandLineTool instead of a Workflow
    #         command_line_tool=fast_cwl_load(                # using fast_cwl_load is safe here because we deal with the content of a file
    #             connexion.request.json["workflow_content"]
    #         )
    #     )
    # )
    # with open(cwl_filename, 'w') as outfile:
    #     outfile.write(formatted_cwl_str)
    
    
    ### run toil script with params
    bash_command = f'bash {script_dir}/run_toil.sh {cwl_filename} {job_filename} {output_folder} {tmp_output_dir} {dag_id} {run_id} {toil_env_file}'
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