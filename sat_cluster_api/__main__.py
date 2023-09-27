import connexion
import urllib
import os
import json
import yaml
from datetime import datetime
import base64
import gzip

# app = connexion.FlaskApp(__name__)

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
    dir_path = os.path.dirname(os.path.realpath(__file__))
    # print(f'dirname: {dir_path}')

    ### save job file
    conf_dict = json.loads(conf)
    output_folder = conf_dict['job']['outputs_folder']
    # remove outputs_folder from job
    del conf_dict['job']['outputs_folder']
    # print(f'config dict: {conf_dict}')
    # print(f'outptus folder: {output_folder}')
    job_filename = f'{dir_path}/{run_id}/job.yml'
    # print(f'file name: {job_filename}')
    os.makedirs(os.path.dirname(job_filename), exist_ok=True)
    with open(job_filename, 'w') as outfile:
        yaml.dump(conf_dict, outfile, default_flow_style=False)
        # print(f'outfile: {outfile}')


    ### save cwl file
    # base64 decode
    # decoded_cwl = base64.decode(workflow_content, 'utf-8')
    # unzip
    # unzipped_cwl = gzip.decompress(workflow_content)#decoded_cwl)
    # print(f'unzipped cwl: {unzipped_cwl}')
    # # save to cwl file
    # cwl_filename = f'{dir_path}/{run_id}/workflow.cwl'
    # with open(cwl_filename, 'w') as outfile:
    #     yaml.dump(unzipped_cwl, outfile, default_flow_style=False)

    ### run toil script with params
    bash_command = f'bash test_script.sh {workflow_content} {job_filename} {output_folder}'
    os.system(f'{bash_command} &')

    start_date_str = datetime.now()
    return {
        'dag_id': dag_id or '1',
        'run_id': run_id or '1',
        'execution_date': start_date_str,
        'start_date': start_date_str,
        'state': 'running'
    }

app.add_api(specification="openapi.yaml")


if __name__ == '__main__':
    # run our standalone gevent server
    app.run(host='127.0.0.1', port=8080)

def run_app():
    app.run(host='127.0.0.1', port=8080)