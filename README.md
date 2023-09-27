

## ENV
python@3.8.12

requires poetry (```pip install poetry```)

## Conda setup

```bash
# setup env
conda create -n cluster-api python=3.8.12
conda activate cluster-api
# setup dependencies
pip isntall poetry
poetry install
```

> poetry chosen for easy builds

## local runs
```bash
poetry run python sat_cluster_api/server.py
# or just
# python sat_cluster_api/server.py
```

then visit [http://localhost:8080/api/experimental/ui/](http://localhost:8080/api/experimental/ui/) for a swagger UI of api