from __future__ import annotations
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass
from xml.etree import ElementTree

import nox
import requests
from packaging.version import parse as parse_version, Version

import os
import time
from typing import List, Union, Dict, Tuple


@dataclass(frozen=True)
class TestedVersions:
    success: Tuple[str, ...]
    failed: Tuple[str, ...]

    @staticmethod
    def _add_version_to_file(
        directory: str, dependency_name: str, dependency_version: str, success: bool
    ):
        dependency_file_path = TestedVersions.get_file_path(directory, dependency_name)
        new_line = f"{'' if success else '!'}{dependency_version}\n"
        print(f"Adding the following line to {dependency_file_path}: {new_line}")
        with open(dependency_file_path, "a") as f:
            f.write(new_line)
        print(
            "DEBUG: dependency file",
            dependency_file_path,
            open(dependency_file_path).read(),
        )

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
            os.path.dirname(__file__)
            + f"/src/test/integration/{directory}/tested_versions/{dependency_name}"
        )

    @staticmethod
    def from_file(path: str) -> TestedVersions:
        success = []
        failed = []
        with open(path, "r") as f:
            for line in f:
                line = line.strip()
                if line.startswith("!"):
                    failed.append(line)
                else:
                    success.append(line)
        return TestedVersions(success=tuple(success), failed=tuple(failed))


def install_package(package_name: str, package_version: str, session) -> None:
    try:
        session.install(f"{package_name}=={package_version}")
    except Exception:
        session.log(f"Cannot install '{package_name}' version '{package_version}'")
        raise


def get_versions_from_pypi(package_name: str) -> List[str]:
    response = requests.get(f"https://pypi.org/rss/project/{package_name}/releases.xml")
    response.raise_for_status()
    xml_tree = ElementTree.fromstring(response.text)
    versions = [i.text for i in xml_tree.findall("channel/item/title") if i.text]
    # Verify all strings have the format for version
    [Version(version) for version in versions]
    return versions


def python_versions() -> Union[List[str], bool]:
    # On Github, just run the current Python version without
    # creating a venv.
    # In local, try all supported python versions building venvs.
    if os.getenv("CI", str(False)).lower() == "true":
        return False

    return ["3.7", "3.8", "3.9", "3.10"]


def should_add_new_versions() -> bool:
    result = os.getenv("ADD_NEW_VERSIONS", "").lower() == "true"
    return result


def dependency_versions(
    directory: str, dependency_name: str, add_new_versions: bool
) -> List[str]:
    """Dependenciy versions are listed in the 'tested_versions/<dependency_name>' files of the instrumentation
    packages, and symlinked under the relevant integration tests. There are also versions in pypi"""
    tested_versions = TestedVersions.from_file(
        TestedVersions.get_file_path(directory, dependency_name)
    )
    if add_new_versions:
        all_tested_versions = tested_versions.success + tested_versions.failed
        pypi_versions = set(get_versions_from_pypi(dependency_name))
        new_versions = list(pypi_versions.difference(all_tested_versions))
        print("running new versions of", dependency_name, new_versions)
        return new_versions
    minor_to_version: Dict[str, Version] = {}
    for version in tested_versions.success:
        parsed_version = parse_version(version)
        minor = f"{parsed_version.major}.{parsed_version.minor}"
        if minor_to_version.get(minor, parse_version("0")) < parsed_version:
            minor_to_version[minor] = parsed_version
    minor_versions = [v.public for v in minor_to_version.values()]
    print("running minor versions of", dependency_name, minor_versions)
    return minor_versions


@nox.session(python=python_versions())
@nox.parametrize(
    "boto3_version",
    dependency_versions(
        directory="boto3",
        dependency_name="boto3",
        add_new_versions=should_add_new_versions(),
    ),
)
def integration_tests_boto3(
    session,
    boto3_version,
):
    with TestedVersions.save_tests_result("boto3", "boto3", boto3_version):
        install_package("boto3", boto3_version, session)

        session.install(".")

        abs_path = os.path.abspath("src/test/integration/boto3/")
        with tempfile.NamedTemporaryFile(suffix=".txt", prefix=abs_path) as temp_file:
            full_path = f"{temp_file}.txt"

            with session.chdir("src/test/integration/boto3"):
                session.install("-r", "requirements_others.txt")

                try:
                    session.run(
                        "sh",
                        "./scripts/start_uvicorn",
                        env={
                            "AUTOWRAPT_BOOTSTRAP": "lumigo_opentelemetry",
                            "LUMIGO_DEBUG_SPANDUMP": full_path,
                            "OTEL_SERVICE_NAME": "app",
                        },
                        external=True,
                    )  # One happy day we will have https://github.com/wntrblm/nox/issues/198

                    # TODO Make this deterministic
                    # Wait 1s to give time for app to start
                    time.sleep(8)

                    session.run(
                        "pytest",
                        "--tb",
                        "native",
                        "--log-cli-level=INFO",
                        "--color=yes",
                        "-v",
                        "./tests/test_boto3.py",
                        env={
                            "LUMIGO_DEBUG_SPANDUMP": full_path,
                        },
                    )
                finally:
                    import psutil

                    # Kill all uvicorn processes
                    for proc in psutil.process_iter():
                        # The python process is names "Python" os OS X and "uvicorn" on CircleCI
                        if proc.name() == "uvicorn":
                            proc.kill()
                        elif proc.name().lower() == "python":
                            cmdline = proc.cmdline()
                            if len(cmdline) > 1 and cmdline[1].endswith("/uvicorn"):
                                proc.kill()

                    session.run("rm", "-f", full_path, external=True)


@nox.session(python=python_versions())
@nox.parametrize(
    "fastapi_version",
    dependency_versions(
        directory="fastapi",
        dependency_name="fastapi",
        add_new_versions=should_add_new_versions(),
    ),
)
def integration_tests_fastapi_fastapi(
    session,
    fastapi_version,
):
    with TestedVersions.save_tests_result("fastapi", "fastapi", fastapi_version):
        integration_tests_fastapi(
            session=session,
            fastapi_version=fastapi_version,
            uvicorn_version="0.17.6",  # arbitrary version
        )


@nox.session(python=python_versions())
@nox.parametrize(
    "uvicorn_version",
    dependency_versions(
        directory="fastapi",
        dependency_name="uvicorn",
        add_new_versions=should_add_new_versions(),
    ),
)
def integration_tests_fastapi_uvicorn(
    session,
    uvicorn_version,
):
    with TestedVersions.save_tests_result("fastapi", "uvicorn", uvicorn_version):
        integration_tests_fastapi(
            session=session,
            fastapi_version="0.78.0",  # arbitrary version
            uvicorn_version=uvicorn_version,
        )


def integration_tests_fastapi(
    session,
    fastapi_version,
    uvicorn_version,
):
    install_package("uvicorn", uvicorn_version, session)
    install_package("fastapi", fastapi_version, session)

    session.install(".")

    abs_path = os.path.abspath("src/test/integration/fastapi/")
    with tempfile.NamedTemporaryFile(suffix=".txt", prefix=abs_path) as temp_file:
        full_path = f"{temp_file}.txt"

        with session.chdir("src/test/integration/fastapi"):
            session.install("-r", "requirements_others.txt")

            try:
                session.run(
                    "sh",
                    "./scripts/start_uvicorn",
                    env={
                        "AUTOWRAPT_BOOTSTRAP": "lumigo_opentelemetry",
                        "LUMIGO_DEBUG_SPANDUMP": full_path,
                        "OTEL_SERVICE_NAME": "app",
                    },
                    external=True,
                )  # One happy day we will have https://github.com/wntrblm/nox/issues/198

                # TODO Make this deterministic
                # Wait 1s to give time for app to start
                time.sleep(8)

                session.run(
                    "pytest",
                    "--tb",
                    "native",
                    "--log-cli-level=INFO",
                    "--color=yes",
                    "-v",
                    "./tests/test_fastapi.py",
                    env={
                        "LUMIGO_DEBUG_SPANDUMP": full_path,
                    },
                )
            finally:
                import psutil

                # Kill all uvicorn processes
                for proc in psutil.process_iter():
                    # The python process is names "Python" os OS X and "uvicorn" on CircleCI
                    if proc.name() == "uvicorn":
                        proc.kill()
                    elif proc.name().lower() == "python":
                        cmdline = proc.cmdline()
                        if len(cmdline) > 1 and cmdline[1].endswith("/uvicorn"):
                            proc.kill()

                session.run("rm", "-f", full_path, external=True)


@nox.session(python=python_versions())
@nox.parametrize(
    "flask_version",
    dependency_versions(
        directory="flask",
        dependency_name="flask",
        add_new_versions=should_add_new_versions(),
    ),
)
def integration_tests_flask(session, flask_version):
    with TestedVersions.save_tests_result("flask", "flask", flask_version):
        install_package("flask", flask_version, session)

        session.install(".")

        abs_path = os.path.abspath("src/test/integration/flask/")
        with tempfile.NamedTemporaryFile(suffix=".txt", prefix=abs_path) as temp_file:
            full_path = f"{temp_file}.txt"

            with session.chdir("src/test/integration/flask"):
                session.install("-r", "requirements_others.txt")

                try:
                    session.run(
                        "sh",
                        "./scripts/start_flask",
                        env={
                            "AUTOWRAPT_BOOTSTRAP": "lumigo_opentelemetry",
                            "LUMIGO_DEBUG_SPANDUMP": full_path,
                            "OTEL_SERVICE_NAME": "app",
                        },
                        external=True,
                    )  # One happy day we will have https://github.com/wntrblm/nox/issues/198

                    # TODO Make this deterministic
                    # Wait 1s to give time for app to start
                    time.sleep(8)

                    session.run(
                        "pytest",
                        "--tb",
                        "native",
                        "--log-cli-level=INFO",
                        "--color=yes",
                        "-v",
                        "./tests/test_flask.py",
                        env={
                            "LUMIGO_DEBUG_SPANDUMP": full_path,
                        },
                    )
                finally:
                    import psutil

                    # Kill all uvicorn processes
                    for proc in psutil.process_iter():
                        # The python process is names "Python" os OS X and "flask" on CircleCI
                        if proc.name() == "flask":
                            proc.kill()
                        elif proc.name().lower() == "python":
                            cmdline = proc.cmdline()
                            if len(cmdline) > 1 and cmdline[1].endswith("/flask"):
                                proc.kill()

                    session.run("rm", "-f", full_path, external=True)


@nox.session(python=python_versions())
@nox.parametrize(
    "pymongo_version",
    dependency_versions(
        directory="pymongo",
        dependency_name="pymongo",
        add_new_versions=should_add_new_versions(),
    ),
)
def integration_tests_pymongo(
    session,
    pymongo_version,
):
    with TestedVersions.save_tests_result("pymongo", "pymongo", pymongo_version):
        install_package("pymongo", pymongo_version, session)

        session.install(".")

        abs_path = os.path.abspath("src/test/integration/pymongo/")
        with tempfile.NamedTemporaryFile(suffix=".txt", prefix=abs_path) as temp_file:
            full_path = f"{temp_file}.txt"

            with session.chdir("src/test/integration/pymongo"):
                session.install("-r", "requirements_others.txt")

                try:
                    session.run(
                        "sh",
                        "./scripts/start_uvicorn",
                        env={
                            "AUTOWRAPT_BOOTSTRAP": "lumigo_opentelemetry",
                            "LUMIGO_DEBUG_SPANDUMP": full_path,
                            "OTEL_SERVICE_NAME": "app",
                        },
                        external=True,
                    )  # One happy day we will have https://github.com/wntrblm/nox/issues/198

                    # TODO Make this deterministic
                    # Wait 1s to give time for app to start
                    time.sleep(8)

                    session.run(
                        "pytest",
                        "--tb",
                        "native",
                        "--log-cli-level=INFO",
                        "--color=yes",
                        "-v",
                        "./tests/test_pymongo.py",
                        env={
                            "LUMIGO_DEBUG_SPANDUMP": full_path,
                        },
                    )
                finally:
                    import psutil

                    # Kill all uvicorn processes
                    for proc in psutil.process_iter():
                        # The python process is names "Python" os OS X and "uvicorn" on CircleCI
                        if proc.name() == "uvicorn":
                            proc.kill()
                        elif proc.name().lower() == "python":
                            cmdline = proc.cmdline()
                            if len(cmdline) > 1 and cmdline[1].endswith("/uvicorn"):
                                proc.kill()

                    session.run("rm", "-f", full_path, external=True)


@nox.session(python=python_versions())
@nox.parametrize(
    "pymysql_version",
    dependency_versions(
        directory="pymysql",
        dependency_name="pymysql",
        add_new_versions=should_add_new_versions(),
    ),
)
def integration_tests_pymysql(
    session,
    pymysql_version,
):
    with TestedVersions.save_tests_result("pymysql", "pymysql", pymysql_version):
        install_package("PyMySQL", pymysql_version, session)

        session.install(".")

        abs_path = os.path.abspath("src/test/integration/pymysql/")
        with tempfile.NamedTemporaryFile(suffix=".txt", prefix=abs_path) as temp_file:
            full_path = f"{temp_file}.txt"

            with session.chdir("src/test/integration/pymysql"):
                session.install("-r", "requirements_others.txt")

                try:
                    session.run(
                        "sh",
                        "./scripts/start_uvicorn",
                        env={
                            "AUTOWRAPT_BOOTSTRAP": "lumigo_opentelemetry",
                            "LUMIGO_DEBUG_SPANDUMP": full_path,
                            "OTEL_SERVICE_NAME": "app",
                        },
                        external=True,
                    )  # One happy day we will have https://github.com/wntrblm/nox/issues/198

                    # TODO Make this deterministic
                    # Wait 1s to give time for app to start
                    time.sleep(8)

                    session.run(
                        "pytest",
                        "--tb",
                        "native",
                        "--log-cli-level=INFO",
                        "--color=yes",
                        "-v",
                        "./tests/test_pymysql.py",
                        env={
                            "LUMIGO_DEBUG_SPANDUMP": full_path,
                        },
                    )
                finally:
                    import psutil

                    # Kill all uvicorn processes
                    for proc in psutil.process_iter():
                        # The python process is names "Python" os OS X and "uvicorn" on CircleCI
                        if proc.name() == "uvicorn":
                            proc.kill()
                        elif proc.name().lower() == "python":
                            cmdline = proc.cmdline()
                            if len(cmdline) > 1 and cmdline[1].endswith("/uvicorn"):
                                proc.kill()

                    session.run("rm", "-f", full_path, external=True)
