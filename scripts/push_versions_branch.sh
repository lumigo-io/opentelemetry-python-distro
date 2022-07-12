if [[ ! `git status --porcelain --untracked-files=no` ]]; then echo "no changes, skipping commit" && exit 0; fi
new_versions=$(./scripts/describe_supported_versions_diff.sh)
git checkout -b $(date +version-testing-%Y%m%d)
git commit -am "Add new supported versions\n\n${new_versions}"x
# git push origin
