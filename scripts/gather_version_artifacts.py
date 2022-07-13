import os
from glob import glob
from typing import List, Dict, Tuple

from ci.tested_versions_utils import TestedVersions

ARTIFACT_DIR_NAME = "versions_artifacts"


def main() -> None:
    runtime_to_files = {
        python_runtime: sorted(
            os.listdir(os.path.join(ARTIFACT_DIR_NAME, python_runtime))
        )
        for python_runtime in os.listdir(ARTIFACT_DIR_NAME)
    }
    print("runtime_to_files:", runtime_to_files)
    if not any(runtime_to_files.values()):
        print("No files were found so nothing to update, returning")
        return
    files_names = list(runtime_to_files.values())[0]
    if any([files != files_names for files in runtime_to_files.values()]):
        raise Exception("Got different files from different runtimes")
    origin_tested_files = glob(
        "src/lumigo_opentelemetry/instrumentations/*/tested_versions/*"
    )
    for file_name in files_names:
        handle_dependency(file_name, origin_tested_files, tuple(runtime_to_files))


def handle_dependency(
    file_name: str, origin_tested_files: List[str], runtimes: Tuple[str, ...]
) -> None:
    print("working on:", file_name)
    origin_path = next(
        path
        for path in origin_tested_files
        if path.endswith(f"tested_versions/{file_name}")
    )
    origin_tested_versions = TestedVersions.from_file(origin_path)
    runtime_to_tested_versions = calculate_runtime_to_tested_versions_dict(
        file_name, runtimes
    )
    version_to_success = calculate_version_to_success_dict(
        origin_tested_versions, runtime_to_tested_versions
    )
    for version, success in version_to_success.items():
        TestedVersions.add_version_to_file(origin_path, version, success)


def calculate_version_to_success_dict(
    origin_tested_versions: TestedVersions,
    runtime_to_tested_versions: Dict[str, TestedVersions],
) -> Dict[str, bool]:
    version_to_success = {}
    origin_versions = set(origin_tested_versions.get_all_versions())
    for runtime, tested_versions in runtime_to_tested_versions.items():
        for version in tested_versions.success:
            if version not in origin_versions and version not in version_to_success:
                version_to_success[version] = True
        for version in tested_versions.failed:
            if version not in origin_versions:
                version_to_success[version] = False
    if not version_to_success:
        print("no new versions found, not writing to file")
    return version_to_success


def calculate_runtime_to_tested_versions_dict(
    file_name: str, runtimes: Tuple[str, ...]
) -> Dict[str, TestedVersions]:
    runtime_to_tested_versions = {
        runtime: TestedVersions.from_file(
            os.path.join(ARTIFACT_DIR_NAME, runtime, file_name)
        )
        for runtime in runtimes
    }
    print("runtime_to_tested_versions:", runtime_to_tested_versions)
    all_versions = sorted(
        list(runtime_to_tested_versions.values())[0].get_all_versions()
    )
    if any(
        [
            sorted(tested_versions.get_all_versions()) != all_versions
            for tested_versions in runtime_to_tested_versions.values()
        ]
    ):
        raise Exception("Got different versions from different runtimes")
    return runtime_to_tested_versions


if __name__ == "__main__":
    main()
