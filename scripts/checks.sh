#!/usr/bin/env bash
set -eo pipefail

pre-commit run -a

if [[ -n "$CI" ]]
then
    # Check if branch contains RD ticket value.
    echo "$GIT_BRANCH"
    echo "$GIT_BRANCH" | grep -E "[RDrd]-[0-9]+|master" || { echo "Please create a relevent ticket in Jira and connect it to this branch. Use jiranch." ; exit 1; }
fi

pushd src
LUMIGO_TRACER_TOKEN='token' py.test --cov=./lumigo_wrapper --cov-config=.coveragerc --ignore=test/integration --ignore=test/components
popd
