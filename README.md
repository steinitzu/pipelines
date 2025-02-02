# Pipelines contrib repo

# Development
`python-dlt` uses `poetry` to manage, build and version the package. It also uses `make` to automate tasks. To start
```sh
make install-poetry  # will install poetry, to be run outside virtualenv
```
then
```sh
make dev  # will install all deps including dev
```
Executing `poetry shell` and working in it is very convenient at this moment.

## python version
Use python 3.8 for development which is the lowest supported version for `python-dlt`. You'll need `distutils` and `venv`:

```shell
sudo apt-get install python3.8
sudo apt-get install python3.8-distutils
sudo apt install python3.8-venv
```
You may also use `pyenv` as [poetry](https://python-poetry.org/docs/managing-environments/) suggests.

## typing and linting
`python-dlt` uses `mypy` and `flake8` with several plugins for linting. We do not reorder imports or reformat code. To lint the code do `make lint`.

**Code does not need to be typed** (but it is better if it is - `mypy` is able to catch a lot of problems in the code)

**Function input argument of sources and resources should be typed** that allows `dlt` to validate input arguments at runtime, say which are secrets and generate the secret and config files automatically.

### Adding __init__.py files
Linting step requires properly constructed python packages so it will ask for `__init__` files to be created. That can be automated with
```sh
./check-package.sh --fix
```
executed from the top repo folder

## Submitting new pipelines or bugfixes

1. Create an issue that describes the pipeline or the problem being fixed
2. Make a feature branch
3. Commit to that branch when you work. Please use descriptive commit names
4. Make a PR to master branch


# Repository structure

All repo code reside in `pipelines` folder. Each pipeline has its own **pipeline folder** (ie. `chess` - see the example) where the `dlt.source` and `dlt.resource` functions are present. The internal organization of this folder is up to the contributor. For each pipeline there's a also a script with the example usages (ie. `chess_pipeline.py`). The intention is to show the user how the sources/resources may be called and let the user to copy the code from it.

## Pipeline specific dependencies.
If pipeline requires additional dependencies that are not available in `python-dlt` they may be added as follows:

1. Use `poetry` to add it to the group with the same name as pipeline. Example: chess pipeline uses `python-chess` to decode game moves. Dependency was added with `poetry add -G chess python-chess`
2. Add `requirements.txt` file in **pipeline folder** and add the dependency there.

## Common code
At some point we can see that many pipelines share common functions. Such common function may be moved to `_helpers` folder and imported from there. (TODO: add documentation when we have a first case)

## Common credentials
All pipeline usage/example scripts share the same config and credential files that are present in `pipelines/.dlt`.

This makes running locally much easier and `dlt` configuration is flexible enough to apply to many pipelines in one folder.

Please look at `example.secrets.toml` in `.dlt` folder on how to configure `postgres`, `redshift` and `bigquery` credentials.

### Adding common credentials

If you add a new pipeline that require secret value, please add a placeholder to `example.secrets.toml`. See example for chess.

# How Pipelines will be used
The reason for the structure above is to use `dlt init` command to let user add the pipelines to their own project. `dlt init` is able to add pipelines as pieces of code, not as dependencies, see explanation here: https://github.com/dlt-hub/python-dlt-init-template

For example if someone issues `dlt init chess bigquery`:

1. `dlt` clones the repo and finds the `chess` in `pipelines` folder.
2. it copies the `chess` folder and `chess_pipeline.py` to user's project folder
3. it modifies the example script `chess_pipeline.py` to use `bigquery` to load data
4. it inspects the `dlt.resource` and `dlt.source` functions in `chess` folder and generates config/credentials sections


# Testing
We use `pytest` for testing. Every test is running within a set of fixtures that provide the following environment (see `conftest.py`):
1. they load secrets and config from `pipelines/.dlt` so the same values are used when you run your pipeline from command line and in tests
2. it sets the working directory for each pipeline to `_storage` folder and makes sure it is empty before each test
3. it drops all datasets from the destination after each test
4. it runs each test with the original environment variables so you can modify `os.environ`

Look at `tests/test_chess_pipeline.py` for an example. The line
```python
@pytest.mark.parametrize('destination_name', ALL_DESTINATIONS)
```
makes sure that each test runs against all destinations (as defined in `ALL_DESTINATIONS` global variables)

The simplest possible test just creates pipeline and then issues a run on a source. More advanced test will use `sql_client` to check the data and access the schemas to check the table structure.


## Test Postgres instance
There's compose file with fully prepared postgres instance [here](tests/postgres/README.md)
