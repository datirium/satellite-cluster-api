import connexion
import os
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
    conf: str, #workflow, #workflow is 'file' type?
    workflow_content: str,
): 
    """
    TODO: 
        - post dag (save to DB if needed)
        - clean up dag runs (stop currently running one since getting this means sample was restarted)
        - start cwlToil based on config and workflow_content
    """
    bash_script = f'echo dag_id:{dag_id} run_id: {run_id} config:{conf} workflow_content:{workflow_content}'
    os.system(bash_script)
    return {
        'dag_id': dag_id or '1',
        'run_id': run_id or '1',
        'execution_date': '',
        'start_date': '',
        'state': 'running'
    }

app.add_api(specification="openapi.yaml")


if __name__ == '__main__':
    # run our standalone gevent server
    app.run(host='127.0.0.1', port=8080)

def run_app():
    app.run(host='127.0.0.1', port=8080)