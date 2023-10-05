# Contributing to the Lumigo OpenTelemetry Distro for Python

Contributions to this project are welcome from all!
Below are a couple pointers on how to prepare your machine, as well as some information on testing.

## Setup

Getting your machine ready to develop against the package is a straightforward process:

1. Clone this repository, and open a CLI in the cloned directory
1. Create a virtual environment for the project `virtualenv venv -p python3`
1. Activate the virtualenv: `. venv/bin/activate`
1. Install dependencies: `pip install -r requirements.txt`
1. Navigate to the source directory: `cd src` and
1. Run the setup script: `python setup.py develop`.
1. Run `pre-commit install` in your repository to install pre-commit hooks

### Psycopg2 installation requirements for MacOS

`Psycopg2` cannot be installed without the `pg_config` executable available, for which you'll need to install `postgres`. For some versions of `Psycopg2`, `libpq` is also required.

You can do this with `brew update && brew install postgresql libpq`.

It might be necessary to throw in a `brew tap homebrew/core` along the way.

### PyCharm Users

If you are using pycharm, ensure that you set it to use the virtualenv virtual environment manager. This is available in the menu under `PyCharm -> Preferences -> Project -> Interpreter`

## Running the test suite

Run `./scripts/checks.sh` in the root folder.

```sh
# Run all the tests
python3 -m nox
# List all the tests
python3 -m nox -l
```

To run specific tests and/or specify Python versions:

* Use `--python PYTHON_VERSION` to specify a Python version eg.

    `--python 3.9`
* Use `-e` to specify a dependency to test eg.

    `python3 -m nox -e integration_tests_flask`
* Use `--session` to specify a dependency and version eg.

    `--session "integration_tests_grpcio(python='3.9', grpcio_version='1.56.0')"`

```sh
# Run a given test with the entire parameter matrix
python3 -m nox -e integration_tests_flask
# Run a given test for a given version of Python and all dependency versions
python -m nox -e integration_tests_grpcio --python 3.9
# Run a given test for a given version of Python and a given dependency version
python -m nox --session "integration_tests_grpcio(python='3.9', grpcio_version='1.56.0')"
```

To run version testing locally, prefix the test command with `TEST_ONLY_UNTESTED_NEW_VERSIONS=true` eg.

```sh
TEST_ONLY_UNTESTED_NEW_VERSIONS=true python3 -m nox -e integration_tests_flask`
```

## Adding support for a new package

The `tested_versions` folder must be present and updated both under `src/lumigo_opentelemetry/instrumentations` and in the tested package's folder under `src/test`. For this to work, you'll need a symlink from the package's `src/test` folder. It's recommended to use the script below to initialize your `tested_versions` folders:

```sh
./scripts/init_tested_versions.sh
```
