

## ENV
python@3.8.12

requires poetry (```pip install poetry```)

## Conda setup

```bash
# setup env
conda create -n cluster-api python=3.8.12
conda activate cluster-api
# setup dependencies
pip install poetry
poetry install
```

> poetry chosen for easy builds

## local runs
```bash
# after running 'poetry install'
start-cluster-api
# or: poetry run start-cluster-api
```

then visit [http://localhost:8081/api/experimental/ui/](http://localhost:8081/api/experimental/ui/) for a swagger UI of api


## builds

build package with ```poetry build```
install build with `pip install dist/<FILE_NAME>.whl`
run installed package with `python -m sat_cluster_api`