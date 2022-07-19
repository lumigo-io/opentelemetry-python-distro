from __future__ import annotations

import os
import re
from contextlib import contextmanager
from dataclasses import dataclass
from functools import cmp_to_key
from typing import Tuple, Union

# Major, minor, patch and (non semver standard, suffix)
_semanticVersionPattern = re.compile(r'(!)?(\d+).(\d+).(\d+)([^\s]*)(?:\s*#\s*(.*))?')
_splitVersionFromCommentPattern = re.compile(r'(!)?([^\s]*)(?:\s*#\s*(.*))?')


@dataclass(frozen=True)
class NonSemanticVersion:
    supported: bool
    version: str
    comment: str


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


def _compare_numbers(first: int, second: int) -> int:
    return (first - second) - (second - first)


def _compare_strings(first: str, second: str) -> int:
    return 0 if (first == second) else (1 if first > second else -1)


def compare_versions(v1: Union[SemanticVersion, NonSemanticVersion], v2: Union[SemanticVersion, NonSemanticVersion]) -> int:
    if isinstance(v1, NonSemanticVersion) and isinstance(v2, NonSemanticVersion):
        # Neither are valid semver, return lexographic order of the versions and comments
        return _compare_strings(v1.version, v2.version) or _compare_strings(v1.comment, v2.comment)

    if isinstance(v1, NonSemanticVersion) and isinstance(v2, SemanticVersion):
        # SemVer comes first
        return 1

    if isinstance(v1, SemanticVersion) and isinstance(v2, NonSemanticVersion):
        # SemVer comes first
        return -1

    # Both are semver
    return (
        _compare_numbers(v1.major, v2.major) or
        _compare_numbers(v1.minor, v2.minor) or
        _compare_numbers(v1.patch, v2.patch) or
        _compare_strings(v1.comment, v2.comment)
    )


def parseVersion(version: str) -> Union[SemanticVersion, NonSemanticVersion]:
    res = re.search(_semanticVersionPattern, version)

    if res:
        (supported, major, minor, patch, suffix, comment) = res.groups()
        # The `supported` is either an emopty string (supported) or the '!' string (not supported)
        print(f"'{version}': {not bool(supported)}, {major}, {minor}, {patch}, {suffix}, {comment}")
        return SemanticVersion(not bool(supported), int(major), int(minor), int(patch), suffix, comment)

    (supported, version, comment) = re.search(_splitVersionFromCommentPattern, version).groups()
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

        parsed_version = parseVersion(('' if supported else '!') + version)

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
            for version in sorted(tested_versions.versions, key=cmp_to_key(compare_versions)):
                if not version.supported:
                    f.write('!')

                f.write(version.version)

                if comment := version.comment:
                    f.write(' # ' + comment)

                f.write('\n')

    @staticmethod
    @contextmanager
    def save_tests_result(
        directory: str, dependency_name: str, dependency_version: str
    ):
        if should_add_new_versions():
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
            return TestedVersions([
                parseVersion(line)
                for line in f
            ])

    def get_all_versions(self) -> Tuple[str, ...]:
        return [
            entry.version
            for entry in versions
        ]


def should_add_new_versions() -> bool:
    return os.getenv("ADD_NEW_VERSIONS", "").lower() == "true"
