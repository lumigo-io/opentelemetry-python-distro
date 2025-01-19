#!/usr/bin/env bash
set -eo pipefail

# pre-commit
pre-commit run -a

# run u.t
pushd src/test
    pytest ci
    pytest unit
popd

# update the README's package compatibility matrix
python3 -m scripts.update_supported_packages_documentation
