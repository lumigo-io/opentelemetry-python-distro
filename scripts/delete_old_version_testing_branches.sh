#!/bin/bash

set -eo pipefail

today=$(date +%Y%m%d)
echo "today: $today"
git fetch --prune
version_testing_branches=$(git branch -r | grep -E '(version-testing-[0-9]{8})' | grep -v "$today" | awk -F'/' '{print $2}')
echo "branches to be removed:"
echo "$version_testing_branches"
echo "$version_testing_branches" | xargs -I {} git push origin --delete {}
