from __future__ import annotations
import os
import tempfile
from xml.etree import ElementTree
import time
from typing import List, Union

import nox
import requests
import yaml

from src.ci.tested_versions_utils import (
    NonSemanticVersion,
    SemanticVersion,
    TestedVersions,
    should_test_only_untested_versions,
)


def install(session, *args) -> None:
    """
    When running in CI we don't use venv and without venv `session.install` is deprecated.
    """
    if session.python is False:  # this means no venv
        session.run("pip", "install", *args)
    else:
        session.install(*args)


def install_package(package_name: str, package_version: str, session) -> None:
    try:
        install(session, f"{package_name}=={package_version}")
    except Exception:
        session.log(f"Cannot install '{package_name}' version '{package_version}'")
        raise


def get_versions_from_pypi(package_name: str) -> List[str]:
    response = requests.get(f"https://pypi.org/rss/project/{package_name}/releases.xml")
    response.raise_for_status()
    xml_tree = ElementTree.fromstring(response.text)
    return [i.text for i in xml_tree.findall("channel/item/title") if i.text]


def python_versions() -> Union[List[str], bool]:
    # On Github, just run the current Python version without
    # creating a venv.
    # In local, try all supported python versions building venvs.
    if os.getenv("CI", str(False)).lower() == "true":
        return False

    with open(
        os.path.dirname(__file__) + "/.github/workflows/nightly-actions.yml"
    ) as f:
        github_workflow = yaml.load(f, Loader=yaml.FullLoader)
        return github_workflow["jobs"]["check-new-versions-of-instrumented-packages"][
            "strategy"
        ]["matrix"]["python-version"]


def get_new_version_from_pypi(
    dependency_name: str, tested_versions: TestedVersions
) -> List[str]:
    pypi_versions = set(get_versions_from_pypi(dependency_name))
    new_versions = list(pypi_versions.difference(set(tested_versions.all_versions)))
    print("running new versions of", dependency_name, new_versions)
    return new_versions


def dependency_versions_to_be_tested(
    directory: str, dependency_name: str, test_untested_versions: bool
) -> List[str]:
    """Dependency versions are listed in the 'tested_versions/<dependency_name>' files of the instrumentation
    packages, and symlinked under the relevant integration tests. There are also versions in pypi"""
    tested_versions = TestedVersions.from_file(
        TestedVersions.get_file_path(directory, dependency_name)
    )
    if test_untested_versions:
        return get_new_version_from_pypi(dependency_name, tested_versions)

    # To avoid unbearable build times, we only retest the last patch of each minor.
    # These versions are already sorted. We use the full object representation,
    # rather than `TestedVersions.supported_versions`, as we need to perform
    # logic on major, minor and patch.
    supported_versions: List[Union[SemanticVersion, NonSemanticVersion]] = list(
        filter(
            lambda tested_version: tested_version.supported,
            tested_versions.versions,
        )
    )

    if len(supported_versions) == 1:
        # Only one version? We surely want to test it!
        return supported_versions

    supported_versions_to_test = []
    for i in range(len(supported_versions))[1:]:
        # Iterate from the second element so that we can look back and
        # detect a change in minor and major
        previous_version = supported_versions[i - 1]
        current_version = supported_versions[i]

        if isinstance(previous_version, NonSemanticVersion):
            # There is no concept of 'minor' and 'patch' in non-semantic version,
            # so we gotta test 'em all
            supported_versions_to_test.append(previous_version)
        elif isinstance(current_version, NonSemanticVersion):
            # The 'next' version is non-semantic, so we are guaranteed
            # that the last version is the last in its series
            supported_versions_to_test.append(previous_version)
        else:
            # Both previous and current are semantic versions
            if (
                previous_version.major < current_version.major
                or previous_version.minor < current_version.minor
            ):
                # Break in major or minor version; the previous_version is
                # the last in its series
                supported_versions_to_test.append(previous_version)

    # By definition, the biggest version is one we want to test
    supported_versions_to_test.append(supported_versions[len(supported_versions) - 1])

    return [
        supported_version_to_test.version
        for supported_version_to_test in supported_versions_to_test
    ]


@nox.session(python=python_versions())
@nox.parametrize(
    "boto3_version",
    dependency_versions_to_be_tested(
        directory="boto3",
        dependency_name="boto3",
        test_untested_versions=should_test_only_untested_versions(),
    ),
)
def integration_tests_boto3(
    session,
    boto3_version,
):
    with TestedVersions.save_tests_result("boto3", "boto3", boto3_version):
        install_package("boto3", boto3_version, session)

        install(session, ".")

        abs_path = os.path.abspath("src/test/integration/boto3/")
        with tempfile.NamedTemporaryFile(suffix=".txt", prefix=abs_path) as temp_file:
            full_path = f"{temp_file}.txt"

            with session.chdir("src/test/integration/boto3"):
                install(session, "-r", "requirements_others.txt")

                try:
                    session.run(
                        "sh",
                        "./scripts/start_uvicorn",
                        env={
                            "AUTOWRAPT_BOOTSTRAP": "lumigo_opentelemetry",
                            "LUMIGO_DEBUG_SPANDUMP": full_path,
                            "OTEL_SERVICE_NAME": "app",
                            "OTEL_RESOURCE_ATTRIBUTES": "K0=V0,K1=V1",  # for testing OTELResourceDetector
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
    dependency_versions_to_be_tested(
        directory="fastapi",
        dependency_name="fastapi",
        test_untested_versions=should_test_only_untested_versions(),
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
    dependency_versions_to_be_tested(
        directory="fastapi",
        dependency_name="uvicorn",
        test_untested_versions=should_test_only_untested_versions(),
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

    install(session, ".")

    abs_path = os.path.abspath("src/test/integration/fastapi/")
    with tempfile.NamedTemporaryFile(suffix=".txt", prefix=abs_path) as temp_file:
        full_path = f"{temp_file}.txt"

        with session.chdir("src/test/integration/fastapi"):
            install(session, "-r", "requirements_others.txt")

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
    dependency_versions_to_be_tested(
        directory="flask",
        dependency_name="flask",
        test_untested_versions=should_test_only_untested_versions(),
    ),
)
def integration_tests_flask(session, flask_version):
    with TestedVersions.save_tests_result("flask", "flask", flask_version):
        install_package("flask", flask_version, session)

        install(session, ".")

        abs_path = os.path.abspath("src/test/integration/flask/")
        with tempfile.NamedTemporaryFile(suffix=".txt", prefix=abs_path) as temp_file:
            full_path = f"{temp_file}.txt"

            with session.chdir("src/test/integration/flask"):
                install(session, "-r", "requirements_others.txt")

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
    dependency_versions_to_be_tested(
        directory="pymongo",
        dependency_name="pymongo",
        test_untested_versions=should_test_only_untested_versions(),
    ),
)
def integration_tests_pymongo(
    session,
    pymongo_version,
):
    with TestedVersions.save_tests_result("pymongo", "pymongo", pymongo_version):
        install_package("pymongo", pymongo_version, session)

        install(session, ".")

        abs_path = os.path.abspath("src/test/integration/pymongo/")
        with tempfile.NamedTemporaryFile(suffix=".txt", prefix=abs_path) as temp_file:
            full_path = f"{temp_file}.txt"

            with session.chdir("src/test/integration/pymongo"):
                install(session, "-r", "requirements_others.txt")

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
    dependency_versions_to_be_tested(
        directory="pymysql",
        dependency_name="pymysql",
        test_untested_versions=should_test_only_untested_versions(),
    ),
)
def integration_tests_pymysql(
    session,
    pymysql_version,
):
    with TestedVersions.save_tests_result("pymysql", "pymysql", pymysql_version):
        install_package("PyMySQL", pymysql_version, session)

        install(session, ".")

        abs_path = os.path.abspath("src/test/integration/pymysql/")
        with tempfile.NamedTemporaryFile(suffix=".txt", prefix=abs_path) as temp_file:
            full_path = f"{temp_file}.txt"

            with session.chdir("src/test/integration/pymysql"):
                install(session, "-r", "requirements_others.txt")

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
