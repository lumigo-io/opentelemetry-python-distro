#!/usr/bin/env bash
set -eo pipefail

python_version="$1"
if [[ -z "$python_version" ]]
then
    python_version="3.9.9"
fi
pyenv local "$python_version"
echo "Creating virtual env using python version: ${python_version}..."

rm -rf venv
python3 -m venv venv
. venv/bin/activate
pip uninstall lumigo_opentelemetry -y
pip install -e .
pip install -r requirements.txt

pre-commit install

scripts/checks.sh
