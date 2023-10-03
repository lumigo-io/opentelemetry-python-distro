#!/usr/bin/env bash

set -eo pipefail

today=$(date +%Y%m%d)
echo "today: $today"
git fetch --unshallow --force
echo "gathering version testing branches..."
version_testing_branches=$(\
    git branch -r \
    | grep -E '(version-testing-[0-9]{8})' || echo "" \
    | grep -v "$today" || echo "" \
    | awk -F'/' '{print $2}'\
)
if [ -z "$version_testing_branches" ]; then
    echo "No version testing branches need to be removed."
    exit 0
fi
echo "branches to be removed:"
echo "$version_testing_branches"
echo "removing branches..."
echo "$version_testing_branches" | xargs -I {} git push origin --delete {}
