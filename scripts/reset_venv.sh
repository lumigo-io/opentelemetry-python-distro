#!/usr/bin/env bash
set -eo pipefail

python_version=$1
if [[ -n "$python_version" ]]
then
    pyenv local "$python_version"
else
    pyenv local "3.9.9"
fi

rm -rf venv
python3 -m venv venv
. venv/bin/activate
pip uninstall lumigo_opentelemetry -y
pip install -e .
pip install -r requirements.txt

pre-commit install

scripts/checks.sh
