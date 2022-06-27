# Contributing to the Lumigo OpenTelemetry Distro for Python

Contributions to this project are welcome from all!
Below are a couple pointers on how to prepare your machine, as well as some information on testing.

### Setup

Getting your machine ready to develop against the package is a straightforward process:

1. Clone this repository, and open a CLI in the cloned directory
1. Create a virtual environment for the project `virtualenv venv -p python3`
1. Activate the virtualenv: `. venv/bin/activate`
1. Install dependencies: `pip install -r requirements.txt`
1. Navigate to the source directory: `cd src` and 
1. Run the setup script: `python setup.py develop`.
1. Run `pre-commit install` in your repository to install pre-commit hooks

**Note**: If you are using pycharm, ensure that you set it to use the virtualenv virtual environment manager. This is available in the menu under `PyCharm -> Preferences -> Project -> Interpreter`

### Running the test suite

Run `./scripts/checks.sh` in the root folder.
