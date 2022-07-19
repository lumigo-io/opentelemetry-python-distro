from __future__ import annotations

import os
import re
from contextlib import contextmanager
from dataclasses import dataclass
from typing import List, Union

# Major, minor, patch and (non semver standard, suffix)
_semanticVersionPattern = re.compile(r'(!)?(\d+).(\d+).(\d+)([^\s]*)(?:\s*#\s*(.*))?')
_splitVersionFromCommentPattern = re.compile(r'(!)?([^\s]*)(?:\s*#\s*(.*))?')

# This file implements a custom version parsing and sorting mechanism,
# as `packaging.version` has strange behaviors that won't work for other
# languages, like:
#
# ```
# >>> from packaging.version import parse
# >>> str(parse("1.2.4c"))
# '1.2.4rc0'
# ```
#
# ```
# >>> from packaging.version import parse
# >>> str(parse("1.2.4b"))
# '1.2.4b0'
# ```


@dataclass(frozen=True)
class NonSemanticVersion:
    supported: bool
    version: str
    comment: str

    def __eq__(self, other):
        if not isinstance(other, NonSemanticVersion):
           return False

        return self.version == other.version

    def __lt__(self, other):
        if not isinstance(other, NonSemanticVersion):
           return False

        return self.version < other.version


@dataclass(frozen=True)
class SemanticVersion:
    supported: bool
    major: int
    minor: int
    patch: int
    suffix: str
    comment: str

    @property
    def version(self):
        return f"{self.major}.{self.minor}.{self.patch}{self.suffix or ''}"

    def __eq__(self, other):
        if not isinstance(other, SemanticVersion):
           return False

        return (
            self.major == other.major and
            self.minor == other.minor and
            self.patch == other.patch and
            self.suffix == other.suffix
        )

    def __lt__(self, other):
        if not isinstance(other, SemanticVersion):
           return True

        if self.major < other.major:
            return True

        if self.major > other.major:
            return False

        if self.minor < other.minor:
            return True

        if self.minor > other.minor:
            return False

        if self.patch < other.patch:
            return True

        if self.patch > other.patch:
            return False

        if not self.suffix and self.suffix:
            return True

        if self.suffix and not self.suffix:
            return False

        return self.suffix < other.suffix


def parse_version(version: str) -> Union[SemanticVersion, NonSemanticVersion]:
    res = re.search(_semanticVersionPattern, version)

    if res:
        (supported, major, minor, patch, suffix, comment) = res.groups()
        # The `supported` is either an empty string (supported) or the '!' string (not supported)
        return SemanticVersion(not bool(supported), int(major), int(minor), int(patch), suffix, comment)

    (supported, version, comment) = re.search(_splitVersionFromCommentPattern, version).groups()
    # The `supported` is either an empty string (supported) or the '!' string (not supported)
    return NonSemanticVersion(not bool(supported), version, comment)


@dataclass(frozen=True)
class TestedVersions:
    versions: List[Union[SemanticVersion, NonSemanticVersion]]

    @staticmethod
    def _add_version_to_file(
        directory: str, dependency_name: str, dependency_version: str, supported: bool
    ):
        dependency_file_path = TestedVersions.get_file_path(directory, dependency_name)
        TestedVersions.add_version_to_file(
            dependency_file_path, dependency_version, supported
        )

    @staticmethod
    def add_version_to_file(path: str, version: str, supported: bool):
        tested_versions = TestedVersions.from_file(path)

        parsed_version = parse_version(('' if supported else '!') + version)

        try:
            previous_version = next(filter(lambda v: v.version == parsed_version.version, tested_versions.versions))
        except StopIteration:
            # This version does not appear in the file
            previous_version = None
            pass

        tested_versions.versions.append(parsed_version)
        if previous_version:
            tested_versions.versions.remove(previous_version)

            if parsed_version.supported == previous_version.supported:
                print(f"Version '{parsed_version.version}' already marked as {'supported' if parsed_version.supported else 'not supported'} in {path}")
            else:
                print(f"Turning version '{parsed_version.version}' to {'supported' if parsed_version.supported else 'not supported'} in {path}")

            if parsed_version.comment != previous_version.comment:
                if parsed_version.comment:
                    print(f"Updating comment for version '{parsed_version.version}' in {path}")
                else:
                    print(f"Removing comment for version '{parsed_version.version}' in {path}")
        else:
            print(f"Adding the {parsed_version.version} as {'supported' if parsed_version.supported else 'not supported'} to {path}")

        with open(path, "w") as f:
            for tested_version in sorted(tested_versions.versions):
                if not tested_version.supported:
                    f.write('!')

                f.write(tested_version.version)

                if tested_version.comment:
                    f.write(' # ' + tested_version.comment)

                f.write('\n')

    @staticmethod
    @contextmanager
    def save_tests_result(
        directory: str, dependency_name: str, dependency_version: str
    ):
        if should_test_only_untested_versions():
            try:
                yield
            except Exception:
                TestedVersions._add_version_to_file(
                    directory, dependency_name, dependency_version, False
                )
                raise
            TestedVersions._add_version_to_file(
                directory, dependency_name, dependency_version, True
            )
        else:
            yield

    @staticmethod
    def get_file_path(directory: str, dependency_name: str) -> str:
        return (
            os.path.dirname(os.path.dirname(__file__))
            + f"/test/integration/{directory}/tested_versions/{dependency_name}"
        )

    @staticmethod
    def from_file(path: str) -> TestedVersions:
        with open(path, 'r') as f:
            # Sort versions on creation
            return TestedVersions(sorted([
                parse_version(line)
                for line in f
            ]))

    @property
    def supported_versions(self) -> List[str]:
        """Return all supported versions, sorted"""
        return [
            tested_version.version
            for tested_version in self.versions
            if tested_version.supported
        ]

    @property
    def unsupported_versions(self) -> List[str]:
        """Return all unsupported versions, sorted"""
        return [
            tested_version.version
            for tested_version in self.versions
            if not tested_version.supported
        ]

    @property
    def all_versions(self) -> List[str]:
        """Return all versions, sorted"""
        return [
            tested_version.version
            for tested_version in self.versions
        ]


def should_test_only_untested_versions() -> bool:
    return os.getenv("TEST_ONLY_UNTESTED_NEW_VERSIONS", "").lower() == "true"
