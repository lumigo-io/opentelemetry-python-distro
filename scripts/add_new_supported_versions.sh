#!/bin/bash

set -euo pipefail

# This script crawls the content of the repository looking for the
# <instrumentation_folder>/supported_versions/<package_name> files,
# when checks on Pypi if there are new versions parsing the RSS with
# some Perl-based XPath, and then checks for each version if it is
# already in the file as a line starting with the version and, if
# not, it appends to the end of it.
# Dependencies: apt install libxml-xpath-perl [Debian]

readonly SCRIPT_DIR="$( cd -- "$( dirname -- "${BASH_SOURCE[0]:-$0}"; )" &> /dev/null && pwd 2> /dev/null; )";
readonly ROOT_DIR="$(dirname ${SCRIPT_DIR})"

# Find all the "supported_version" files and see if they need update
find "${ROOT_DIR}/src/" -path */supported_versions/* | \
    while read -r version_file; do \
        if [ -n "$(tail -c 1 ${version_file})" ]; then
            >&2 echo "Adding missing newline at the end of ${version_file}"
            echo >> "${version_file}"
        fi
        package_name=$(basename "${version_file}")
        >&2 echo "Looking for new versions of package ${package_name}"

        curl -s https://pypi.org/rss/project/${package_name}/releases.xml | \
        xpath -q -e '/rss/channel/item/title/text()' | \
        sort -r | \
        while read -r version; do \
            if ! grep "^${version}" "${version_file}" > /dev/null; then
                echo "${version}" >> "${version_file}"
                >&2 echo "Found new version '${version}'"
            fi
        done
    done
