# lumigo-python-wrapper :stars:
![Version](https://img.shields.io/badge/version-1.0.1012-green.svg) [![CircleCI](https://circleci.com/gh/lumigo-io/lumigo-node-wrapper/tree/master.svg?style=svg&circle-token=488f0e5cc37e20e9a85123a3afe3457a5efdcc55)](https://circleci.com/gh/lumigo-io/lumigo-node-wrapper/tree/master)

This is [`lumigo-python-wrapper`](https://), Lumigo's Python tracer for distributed tracing and performance monitoring.

Supported Python Runtimes: 3.6, 3.7, 3.8

# Usage

# Manually

# Contributing

Contributions to this project are welcome from all! Below are a couple pointers on how to prepare your machine, as well as some information on testing.

## Preparing your machine
Getting your machine ready to develop against the package is a straightforward process:

1. Clone this repository, and open a CLI in the cloned directory
1. Create a virtual environment for the project `virtualenv venv -p python3`
1. Activate the virtualenv: `. venv/bin/activate`
1. Install dependencies: `pip install -r requirements.txt`
1. Navigate to the source directory: `cd src` and 
1. Run the setup script: `python setup.py develop`.
1. Run `pre-commit install` in your repository to install pre-commit hooks

**Note**: If you are using pycharm, ensure that you set it to use the virtualenv virtual environment manager. This is available in the menu under PyCharm -> Preferences -> Project -> Interpreter


## Running the test suite
We've provided an easy way to run the unit test suite:
* Run `./scripts/checks.sh` in the root folder.
