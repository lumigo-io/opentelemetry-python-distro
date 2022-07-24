#!/usr/bin/env bash
set -eo pipefail

python3 -m pre-commit run -a
pushd src
LUMIGO_TRACER_TOKEN='token' py.test --cov=./lumigo_wrapper --cov-config=.coveragerc --ignore=test/integration
popd