from __future__ import annotations

import os
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class TestedVersions:
    success: Tuple[str, ...]
    failed: Tuple[str, ...]

    @staticmethod
    def _add_version_to_file(
        directory: str, dependency_name: str, dependency_version: str, success: bool
    ):
        dependency_file_path = TestedVersions.get_file_path(directory, dependency_name)
        TestedVersions.add_version_to_file(
            dependency_file_path, dependency_version, success
        )

    @staticmethod
    def add_version_to_file(path: str, version: str, success: bool):
        new_line = f"{'' if success else '!'}{version}\n"
        print(f"Adding the following line to {path}: {new_line}")
        with open(path, "a") as f:
            f.write(new_line)

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
        success = []
        failed = []
        with open(path, "r") as f:
            for line in f:
                line = line.strip()
                if line.startswith("!"):
                    failed.append(line[1:])
                else:
                    success.append(line)
        return TestedVersions(success=tuple(success), failed=tuple(failed))

    def get_all_versions(self) -> Tuple[str, ...]:
        return self.success + self.failed


def should_add_new_versions() -> bool:
    return os.getenv("ADD_NEW_VERSIONS", "").lower() == "true"
