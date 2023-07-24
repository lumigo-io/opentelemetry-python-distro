from __future__ import annotations
import os
import psutil
import re
import sys
import tempfile
import time
from typing import List, Union, Optional
from xml.etree import ElementTree

import nox
import requests
import yaml

# Ensure nox can load local packages
repo_dir = os.path.dirname(__file__)
if repo_dir not in sys.path:
    sys.path.append(repo_dir)

from src.ci.tested_versions_utils import (  # noqa: E402
    NonSemanticVersion,
    SemanticVersion,
    TestedVersions,
    should_test_only_untested_versions,
)

OTHER_REQUIREMENTS = "requirements_others.txt"


def create_component_tempfile(name: str):
    temp_file = tempfile.NamedTemporaryFile(
        suffix=".txt",
        prefix=f"temp_{name}_",
        dir=os.path.abspath("src/test/components/"),
        delete=False,
    )
    temp_file.close()
    return temp_file.name


def create_it_tempfile(name: str):
    temp_file = tempfile.NamedTemporaryFile(
        suffix=".txt",
        prefix="temp_",
        dir=os.path.abspath(f"src/test/integration/{name}/"),
        delete=False,
    )
    temp_file.close()
    return temp_file.name


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
    return [i.text for i in xml_tree.findall("channel/item/title") if i.text]


def python_versions() -> Optional[List[str]]:
    # On Github, just run the current Python version.
    # In local, try all supported python versions.
    # Anyway create a venv.
    if os.getenv("CI", str(False)).lower() == "true":
        return None

    with open(
        os.path.dirname(__file__) + "/.github/workflows/version-testing.yml"
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


@nox.session()
def list_integration_tests_ci(session):
    integration_tests = {
        session_runner.name
        for (session_runner, _) in session._runner.manifest.list_all_sessions()
        if session_runner.name.startswith("integration_tests_")
    }

    for i in integration_tests:
        print(i)


@nox.session(python=python_versions())
@nox.parametrize(
    "boto3_version",
    dependency_versions_to_be_tested(
        directory="boto3",
        dependency_name="boto3",
        test_untested_versions=should_test_only_untested_versions(),
    ),
)
def integration_tests_boto3_sqs(
    session,
    boto3_version,
):
    with TestedVersions.save_tests_result("boto3-sqs", "boto3", boto3_version):
        install_package("boto3", boto3_version, session)

        session.install(".")

        temp_file = create_it_tempfile("boto3-sqs")
        with session.chdir("src/test/integration/boto3-sqs"):
            session.install("-r", OTHER_REQUIREMENTS)

            try:
                session.run(
                    "sh",
                    "./scripts/run_app",
                    env={
                        "LUMIGO_DEBUG_SPANDUMP": temp_file,
                    },
                    external=True,
                )  # One happy day we will have https://github.com/wntrblm/nox/issues/198

                # TODO Make this deterministic
                # Give time for app to start
                time.sleep(8)

                session.run(
                    "pytest",
                    "--tb",
                    "native",
                    "--log-cli-level=INFO",
                    "--color=yes",
                    "-v",
                    "./tests/test_boto3_sqs.py",
                    env={
                        "LUMIGO_DEBUG_SPANDUMP": temp_file,
                    },
                )
            finally:
                kill_process_and_clean_outputs(temp_file, "run_app", session)


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

        session.install(".")

        temp_file = create_it_tempfile("boto3")
        with session.chdir("src/test/integration/boto3"):
            session.install("-r", OTHER_REQUIREMENTS)

            try:
                session.run(
                    "sh",
                    "./scripts/start_uvicorn",
                    env={
                        "AUTOWRAPT_BOOTSTRAP": "lumigo_opentelemetry",
                        "LUMIGO_DEBUG_SPANDUMP": temp_file,
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
                        "LUMIGO_DEBUG_SPANDUMP": temp_file,
                    },
                )
            finally:
                kill_process_and_clean_outputs(temp_file, "uvicorn", session)


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

    session.install(".")

    temp_file = create_it_tempfile("fastapi")
    with session.chdir("src/test/integration/fastapi"):
        session.install("-r", OTHER_REQUIREMENTS)

        try:
            session.run(
                "sh",
                "./scripts/start_uvicorn",
                env={
                    "AUTOWRAPT_BOOTSTRAP": "lumigo_opentelemetry",
                    "LUMIGO_DEBUG_SPANDUMP": temp_file,
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
                    "LUMIGO_DEBUG_SPANDUMP": temp_file,
                },
            )
        finally:
            kill_process_and_clean_outputs(temp_file, "uvicorn", session)


@nox.session(python=python_versions())
def component_tests(session):
    component_tests_attr_max_size(
        session=session,
        fastapi_version="0.78.0",  # arbitrary version
        uvicorn_version="0.16.0",  # arbitrary version
    )
    component_tests_execution_tags(
        session=session,
        fastapi_version="0.78.0",  # arbitrary version
        uvicorn_version="0.16.0",  # arbitrary version
    )


def component_tests_attr_max_size(
    session,
    fastapi_version,
    uvicorn_version,
):
    install_package("uvicorn", uvicorn_version, session)
    install_package("fastapi", fastapi_version, session)

    session.install(".")

    temp_file = create_component_tempfile("attr_max_size")
    with session.chdir("src/test/components"):
        session.install("-r", OTHER_REQUIREMENTS)

        try:
            session.run(
                "sh",
                "./scripts/start_uvicorn",
                env={
                    "AUTOWRAPT_BOOTSTRAP": "lumigo_opentelemetry",
                    "LUMIGO_DEBUG_SPANDUMP": temp_file,
                    "OTEL_SERVICE_NAME": "app",
                    "OTEL_SPAN_ATTRIBUTE_VALUE_LENGTH_LIMIT": "1",
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
                "./tests/test_attr_max_size.py",
                env={
                    "LUMIGO_DEBUG_SPANDUMP": temp_file,
                    "OTEL_SPAN_ATTRIBUTE_VALUE_LENGTH_LIMIT": "1",
                },
            )
        finally:
            kill_process_and_clean_outputs(temp_file, "uvicorn", session)


def component_tests_execution_tags(
    session,
    fastapi_version,
    uvicorn_version,
):
    install_package("uvicorn", uvicorn_version, session)
    install_package("fastapi", fastapi_version, session)

    session.install(".")

    temp_file = create_component_tempfile("execution_tags")
    with session.chdir("src/test/components"):
        session.install("-r", OTHER_REQUIREMENTS)

        try:
            session.run(
                "sh",
                "./scripts/start_uvicorn",
                env={
                    "AUTOWRAPT_BOOTSTRAP": "lumigo_opentelemetry",
                    "LUMIGO_DEBUG_SPANDUMP": temp_file,
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
                "./tests/test_execution_tags.py",
                env={
                    "LUMIGO_DEBUG_SPANDUMP": temp_file,
                },
            )
        finally:
            kill_process_and_clean_outputs(temp_file, "uvicorn", session)


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

        session.install(".")

        temp_file = create_it_tempfile("flask")
        with session.chdir("src/test/integration/flask"):
            session.install("-r", OTHER_REQUIREMENTS)

            try:
                session.run(
                    "sh",
                    "./scripts/start_flask",
                    env={
                        "AUTOWRAPT_BOOTSTRAP": "lumigo_opentelemetry",
                        "LUMIGO_DEBUG_SPANDUMP": temp_file,
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
                        "LUMIGO_DEBUG_SPANDUMP": temp_file,
                    },
                )
            finally:
                kill_process_and_clean_outputs(temp_file, "flask", session)


@nox.session(python=python_versions())
@nox.parametrize(
    "grpcio_version",
    dependency_versions_to_be_tested(
        directory="grpcio",
        dependency_name="grpcio",
        test_untested_versions=should_test_only_untested_versions(),
    ),
)
def integration_tests_grpcio(
    session,
    grpcio_version,
):
    with TestedVersions.save_tests_result("grpcio", "grpcio", grpcio_version):
        install_package("grpcio", grpcio_version, session)

        session.install(".")

        # Some versions of PyMongo fail with older versions of wheel
        session.run(
            "python", "-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel"
        )

        server_spans = tempfile.NamedTemporaryFile(
            suffix=".txt", prefix=create_it_tempfile("grpcio")
        ).name
        client_spans = tempfile.NamedTemporaryFile(
            suffix=".txt", prefix=create_it_tempfile("grpcio")
        ).name
        with session.chdir("src/test/integration/grpcio"):
            session.install("-r", OTHER_REQUIREMENTS)

            try:
                session.run(
                    "sh",
                    "./scripts/start_server",
                    env={
                        "AUTOWRAPT_BOOTSTRAP": "lumigo_opentelemetry",
                        "LUMIGO_DEBUG_SPANDUMP": server_spans,
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
                    "./tests/test_grpcio.py",
                    env={
                        "AUTOWRAPT_BOOTSTRAP": "lumigo_opentelemetry",
                        "SERVER_SPANDUMP": server_spans,
                        "LUMIGO_DEBUG_SPANDUMP": client_spans,
                        "OTEL_SERVICE_NAME": "app",
                    },
                )
            finally:
                kill_process("greeter_server.py")
                clean_outputs(server_spans, session)
                clean_outputs(client_spans, session)


@nox.session(python=python_versions())
@nox.parametrize(
    "kafka_python_version",
    dependency_versions_to_be_tested(
        directory="kafka_python",
        dependency_name="kafka_python",
        test_untested_versions=should_test_only_untested_versions(),
    ),
)
def integration_tests_kafka_python(
    session,
    kafka_python_version,
):
    with TestedVersions.save_tests_result(
        "kafka_python", "kafka_python", kafka_python_version
    ):
        install_package("kafka_python", kafka_python_version, session)

        session.install(".")

        session.run(
            "python", "-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel"
        )

        temp_file = create_it_tempfile("kafka_python")
        with session.chdir("src/test/integration/kafka_python"):
            session.install("-r", OTHER_REQUIREMENTS)

            try:
                session.run(
                    "sh",
                    "./scripts/start_uvicorn",
                    env={
                        "AUTOWRAPT_BOOTSTRAP": "lumigo_opentelemetry",
                        "LUMIGO_DEBUG_SPANDUMP": temp_file,
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
                    "./tests/test_kafka_python.py",
                    env={
                        "LUMIGO_DEBUG_SPANDUMP": temp_file,
                    },
                )
            finally:
                kill_process_and_clean_outputs(temp_file, "uvicorn", session)


@nox.session(python=python_versions())
@nox.parametrize(
    "pika_version",
    dependency_versions_to_be_tested(
        directory="pika",
        dependency_name="pika",
        test_untested_versions=should_test_only_untested_versions(),
    ),
)
def integration_tests_pika(
    session,
    pika_version,
):
    with TestedVersions.save_tests_result("pika", "pika", pika_version):
        install_package("pika", pika_version, session)

        session.install(".")

        session.run(
            "python", "-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel"
        )

        temp_file = create_it_tempfile("pika")
        with session.chdir("src/test/integration/pika"):
            session.install("-r", OTHER_REQUIREMENTS)

            try:
                session.run(
                    "sh",
                    "./scripts/start_uvicorn",
                    env={
                        "AUTOWRAPT_BOOTSTRAP": "lumigo_opentelemetry",
                        "LUMIGO_DEBUG_SPANDUMP": temp_file,
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
                    "./tests/test_pika.py",
                    env={
                        "LUMIGO_DEBUG_SPANDUMP": temp_file,
                    },
                )
            finally:
                kill_process_and_clean_outputs(temp_file, "uvicorn", session)


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
        if (
            str(pymongo_version).startswith("3.")  # is 3.x
            and not re.match(r"3\.\d{2}.*", str(pymongo_version))  # not 3.10.x or above
            # and on a Python version above 3.9
            and sys.version_info.major == 3
            and sys.version_info.minor > 9
        ):
            # PyMongo below '3.10.1' is broken on Python 3.10+
            # because of the removal of the 'collections' package
            # https://github.com/python/cpython/issues/81505
            return

        install_package("pymongo", pymongo_version, session)

        session.install(".")

        # Some versions of PyMongo fail with older versions of wheel
        session.run(
            "python", "-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel"
        )

        temp_file = create_it_tempfile("pymongo")
        with session.chdir("src/test/integration/pymongo"):
            session.install("-r", OTHER_REQUIREMENTS)

            try:
                session.run(
                    "sh",
                    "./scripts/start_uvicorn",
                    env={
                        "AUTOWRAPT_BOOTSTRAP": "lumigo_opentelemetry",
                        "LUMIGO_DEBUG_SPANDUMP": temp_file,
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
                        "LUMIGO_DEBUG_SPANDUMP": temp_file,
                    },
                )
            finally:
                kill_process_and_clean_outputs(temp_file, "uvicorn", session)


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

        session.install(".")

        temp_file = create_it_tempfile("pymysql")
        with session.chdir("src/test/integration/pymysql"):
            session.install("-r", OTHER_REQUIREMENTS)

            try:
                session.run(
                    "sh",
                    "./scripts/start_uvicorn",
                    env={
                        "AUTOWRAPT_BOOTSTRAP": "lumigo_opentelemetry",
                        "LUMIGO_DEBUG_SPANDUMP": temp_file,
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
                        "LUMIGO_DEBUG_SPANDUMP": temp_file,
                    },
                )
            finally:
                kill_process_and_clean_outputs(temp_file, "uvicorn", session)


def kill_process_and_clean_outputs(full_path: str, process_name: str, session) -> None:
    kill_process(process_name)
    clean_outputs(full_path, session)


def kill_process(process_name: str) -> None:
    try:
        # Kill all processes with the given name
        for proc in psutil.process_iter():
            if proc.status() == psutil.STATUS_ZOMBIE:
                continue
            # The python process is names "Python" os OS X and "uvicorn" on CircleCI
            if proc.name() == process_name:
                print(f"Killing process with name {proc.name()}...")
                proc.kill()
            elif proc.name().lower().startswith("python"):
                cmdline = proc.cmdline()
                if len(cmdline) > 1 and cmdline[1].endswith("/" + process_name):
                    print(
                        f"Killing process with name {proc.name()} and cmdline {cmdline}..."
                    )
                    proc.kill()
    except psutil.ZombieProcess as zp:
        print(f"Failed to kill zombie process for {process_name}: {str(zp)}")
    except psutil.NoSuchProcess as nsp:
        print(f"Failed to kill process for {process_name}: {str(nsp)}")


def clean_outputs(full_path: str, session) -> None:
    session.run("rm", "-f", full_path, external=True)


if __name__ == "__main__":
    from nox.__main__ import main

    main()
