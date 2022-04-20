#!/usr/bin/env bash
set -eo pipefail

pre-commit run -a
pushd src
py.test --cov=./lumigo_wrapper --cov-config=.coveragerc
popd