from __future__ import annotations

import os
import platform
import re
import sys
import tempfile
import time
from typing import List, Optional, Union
from xml.etree import ElementTree

import nox
import requests
import yaml

from src.test.test_utils.processes import kill_process

# Ensure nox can load local packages
repo_dir = os.path.dirname(__file__)
if repo_dir not in sys.path:
    sys.path.append(repo_dir)

from src.ci.tested_versions_utils import (  # noqa: E402
    NonSemanticVersion,
    SemanticVersion,
    TestedVersions,
    parse_version,
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
        python_version = parse_version(platform.python_version())
        return [f"{python_version.major}.{python_version.minor}"]

    with open(
        os.path.dirname(__file__) + "/.github/workflows/version-testing.yml"
    ) as f:
        github_workflow = yaml.load(f, Loader=yaml.FullLoader)
        return github_workflow["jobs"]["test-untested-versions"]["strategy"]["matrix"][
            "python-version"
        ]


def get_new_version_from_pypi(
    dependency_name: str, tested_versions: TestedVersions
) -> List[str]:
    pypi_versions = set(get_versions_from_pypi(dependency_name))
    new_versions = list(pypi_versions.difference(set(tested_versions.all_versions)))
    print("running new versions of", dependency_name, new_versions)
    return new_versions


def dependency_versions_to_be_tested(
    python: str,
    directory: str,
    dependency_name: str,
    session: nox.sessions.Session = None,
) -> List[str]:
    """Dependency versions are listed in the 'tested_versions/<python_runtime>/<dependency_name>' files of the instrumentation
    packages, and symlinked under the relevant integration tests. There are also versions in pypi"""
    tested_versions = TestedVersions.from_file(
        TestedVersions.get_file_path(directory, python, dependency_name)
    )
    if should_test_only_untested_versions():
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

    if len(supported_versions) == 0:
        return []

    if len(supported_versions) == 1:
        # if we only have one supported entry in the supported versions
        # file, return its version number so that we'll test it
        return [supported_versions[0].version]

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


def wait_for_app_start():
    # TODO Make this deterministic
    time.sleep(8)


@nox.session()
def list_integration_tests_ci(session):
    integration_tests = {
        session_runner.name
        for (session_runner, _) in session._runner.manifest.list_all_sessions()
        if session_runner.name.startswith("integration_tests_")
    }

    for i in integration_tests:
        print(i)


@nox.session()
@nox.parametrize(
    "python,boto3_version",
    [
        (python, boto3_version)
        for python in python_versions()
        for boto3_version in dependency_versions_to_be_tested(
            python=python,
            directory="boto3",
            dependency_name="boto3",
        )
    ],
)
def integration_tests_boto3_sqs(
    session,
    boto3_version,
):
    python = session.python
    with TestedVersions.save_tests_result("boto3-sqs", python, "boto3", boto3_version):
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


@nox.session()
@nox.parametrize(
    "python,boto3_version",
    [
        (python, boto3_version)
        for python in python_versions()
        for boto3_version in dependency_versions_to_be_tested(
            python=python,
            directory="boto3",
            dependency_name="boto3",
        )
    ],
)
def integration_tests_boto3(
    session,
    boto3_version,
):
    python = session.python
    with TestedVersions.save_tests_result("boto3", python, "boto3", boto3_version):
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

                wait_for_app_start()

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


@nox.session()
@nox.parametrize(
    "python,fastapi_version",
    [
        (python, fastapi_version)
        for python in python_versions()
        for fastapi_version in dependency_versions_to_be_tested(
            python=python,
            directory="fastapi",
            dependency_name="fastapi",
        )
    ],
)
def integration_tests_fastapi_fastapi(
    session,
    fastapi_version,
):
    python = session.python
    with TestedVersions.save_tests_result(
        "fastapi", python, "fastapi", fastapi_version
    ):
        integration_tests_fastapi(
            session=session,
            fastapi_version=fastapi_version,
            uvicorn_version="0.17.6",  # arbitrary version
        )


@nox.session()
@nox.parametrize(
    "python,uvicorn_version",
    [
        (python, uvicorn_version)
        for python in python_versions()
        for uvicorn_version in dependency_versions_to_be_tested(
            python=python,
            directory="fastapi",
            dependency_name="uvicorn",
        )
    ],
)
def integration_tests_fastapi_uvicorn(
    session,
    uvicorn_version,
):
    python = session.python
    with TestedVersions.save_tests_result(
        "fastapi", python, "uvicorn", uvicorn_version
    ):
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
            clean_outputs(temp_file, session)


@nox.session(python=python_versions())
def component_tests(session):
    component_tests_execution_tags(
        session=session,
        fastapi_version="0.78.0",  # arbitrary version
        uvicorn_version="0.16.0",  # TODO don't update, see https://lumigo.atlassian.net/browse/RD-11466
    )


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
            clean_outputs(temp_file, session)


@nox.session()
@nox.parametrize(
    "python,django_version",
    [
        (python, django_version)
        for python in python_versions()
        for django_version in dependency_versions_to_be_tested(
            python=python,
            directory="django",
            dependency_name="django",
        )
    ],
)
def integration_tests_django(session, django_version):
    python = session.python
    with TestedVersions.save_tests_result("django", python, "django", django_version):
        install_package("django", django_version, session)

        session.install(".")

        temp_file = create_it_tempfile("django")
        with session.chdir("src/test/integration/django"):
            session.install("-r", OTHER_REQUIREMENTS)

            try:
                session.run(
                    "sh",
                    "./scripts/start_django",
                    env={
                        "LUMIGO_DEBUG_SPANDUMP": temp_file,
                        "OTEL_SERVICE_NAME": "app",
                    },
                    external=True,
                )  # One happy day we will have https://github.com/wntrblm/nox/issues/198

                wait_for_app_start()

                session.run(
                    "pytest",
                    "--tb",
                    "native",
                    "--log-cli-level=INFO",
                    "--color=yes",
                    "-v",
                    "./tests/test_django.py",
                    env={
                        "LUMIGO_DEBUG_SPANDUMP": temp_file,
                    },
                )
            finally:
                kill_process_and_clean_outputs(temp_file, "manage.py", session)


@nox.session()
@nox.parametrize(
    "python,flask_version",
    [
        (python, flask_version)
        for python in python_versions()
        for flask_version in dependency_versions_to_be_tested(
            python=python,
            directory="flask",
            dependency_name="flask",
        )
    ],
)
def integration_tests_flask(session, flask_version):
    python = session.python
    with TestedVersions.save_tests_result("flask", python, "flask", flask_version):
        install_package("flask", flask_version, session)

        session.install(".")

        temp_file = create_it_tempfile("flask")
        with session.chdir("src/test/integration/flask"):
            session.install("-r", OTHER_REQUIREMENTS)

            # override the default Werkzeug version for flask v2 compatibility
            if flask_version.startswith("2."):
                if python == "3.7":
                    session.install("werkzeug==2.2.3")
                else:
                    session.install("werkzeug==2.3.7")

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

                wait_for_app_start()

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


@nox.session()
@nox.parametrize(
    "python,grpcio_version",
    [
        (python, grpcio_version)
        for python in python_versions()
        for grpcio_version in dependency_versions_to_be_tested(
            python=python,
            directory="grpcio",
            dependency_name="grpcio",
        )
    ],
)
def integration_tests_grpcio(
    session,
    grpcio_version,
):
    python = session.python
    with TestedVersions.save_tests_result("grpcio", python, "grpcio", grpcio_version):
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

                wait_for_app_start()

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


@nox.session()
@nox.parametrize(
    "python,kafka_python_version",
    [
        (python, kafka_python_version)
        for python in python_versions()
        for kafka_python_version in dependency_versions_to_be_tested(
            python=python,
            directory="kafka_python",
            dependency_name="kafka_python",
        )
    ],
)
def integration_tests_kafka_python(
    session,
    kafka_python_version,
):
    python = session.python
    with TestedVersions.save_tests_result(
        "kafka_python", python, "kafka_python", kafka_python_version
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

                wait_for_app_start()

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


@nox.session()
@nox.parametrize(
    "python,motor_version",
    [
        (python, motor_version)
        for python in python_versions()
        for motor_version in dependency_versions_to_be_tested(
            python=python,
            directory="motor",
            dependency_name="motor",
        )
    ],
)
def integration_tests_motor(
    session,
    motor_version,
):
    python = session.python
    with TestedVersions.save_tests_result("motor", python, "motor", motor_version):
        install_package("motor", motor_version, session)

        session.install(".")

        temp_file = create_it_tempfile("motor")
        with session.chdir("src/test/integration/motor"):
            session.install("-r", OTHER_REQUIREMENTS)
            try:
                session.run(
                    "pytest",
                    "--tb",
                    "native",
                    "--log-cli-level=INFO",
                    "--color=yes",
                    "-v",
                    "./tests/test_motor.py",
                    env={
                        "LUMIGO_DEBUG_SPANDUMP": temp_file,
                    },
                )
            finally:
                kill_process_and_clean_outputs(temp_file, "test_motor", session)


@nox.session()
@nox.parametrize(
    "python,pika_version",
    [
        (python, pika_version)
        for python in python_versions()
        for pika_version in dependency_versions_to_be_tested(
            python=python,
            directory="pika",
            dependency_name="pika",
        )
    ],
)
def integration_tests_pika(
    session,
    pika_version,
):
    python = session.python
    with TestedVersions.save_tests_result("pika", python, "pika", pika_version):
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

                wait_for_app_start()

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


@nox.session()
@nox.parametrize(
    "python,dependency_name,psycopg2_version",
    [
        (python, dependency_name, psycopg2_version)
        for python in python_versions()
        for dependency_name in ["psycopg2", "psycopg2-binary"]
        for psycopg2_version in dependency_versions_to_be_tested(
            python=python,
            directory="psycopg2",
            dependency_name=dependency_name,
        )
    ],
)
def integration_tests_psycopg2(
    session,
    dependency_name,
    psycopg2_version,
):
    python = session.python
    with TestedVersions.save_tests_result(
        "psycopg2",
        python,
        dependency_name=dependency_name,
        dependency_version=psycopg2_version,
    ):
        install_package(dependency_name, psycopg2_version, session)

        session.install(".")

        temp_file = create_it_tempfile("psycopg2")
        with session.chdir("src/test/integration/psycopg2"):
            session.install("-r", OTHER_REQUIREMENTS)

            try:
                session.run(
                    "pytest",
                    "--tb",
                    "native",
                    "--log-cli-level=INFO",
                    "--color=yes",
                    "-v",
                    "./tests/test_psycopg2.py",
                    env={
                        "LUMIGO_DEBUG_SPANDUMP": temp_file,
                    },
                )
            finally:
                kill_process_and_clean_outputs(temp_file, "test_psycopg2", session)


@nox.session()
@nox.parametrize(
    "python,pymongo_version",
    [
        (python, pymongo_version)
        for python in python_versions()
        for pymongo_version in dependency_versions_to_be_tested(
            python=python,
            directory="pymongo",
            dependency_name="pymongo",
        )
    ],
)
def integration_tests_pymongo(
    session,
    pymongo_version,
):
    python = session.python
    with TestedVersions.save_tests_result(
        "pymongo", python, "pymongo", pymongo_version
    ):
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

                wait_for_app_start()

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


@nox.session()
@nox.parametrize(
    "python,pymysql_version",
    [
        (python, pymysql_version)
        for python in python_versions()
        for pymysql_version in dependency_versions_to_be_tested(
            python=python,
            directory="pymysql",
            dependency_name="pymysql",
        )
    ],
)
def integration_tests_pymysql(
    session,
    pymysql_version,
):
    python = session.python
    with TestedVersions.save_tests_result(
        "pymysql", python, "pymysql", pymysql_version
    ):
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

                wait_for_app_start()

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


@nox.session()
@nox.parametrize(
    "python,redis_version",
    [
        (python, redis_version)
        for python in python_versions()
        for redis_version in dependency_versions_to_be_tested(
            python=python,
            directory="redis",
            dependency_name="redis",
        )
    ],
)
def integration_tests_redis(
    session,
    redis_version,
):
    python = session.python
    with TestedVersions.save_tests_result("redis", python, "redis", redis_version):
        install_package("redis", redis_version, session)

        session.install(".")

        temp_file = create_it_tempfile("redis")
        with session.chdir("src/test/integration/redis"):
            session.install("-r", OTHER_REQUIREMENTS)

            try:
                session.run(
                    "pytest",
                    "--tb",
                    "native",
                    "--log-cli-level=INFO",
                    "--color=yes",
                    "-v",
                    "./tests/test_redis.py",
                    env={
                        "LUMIGO_DEBUG_SPANDUMP": temp_file,
                    },
                )
            finally:
                kill_process_and_clean_outputs(temp_file, "test_redis", session)


def kill_process_and_clean_outputs(full_path: str, process_name: str, session) -> None:
    kill_process(process_name)
    clean_outputs(full_path, session)


def clean_outputs(full_path: str, session) -> None:
    session.run("rm", "-f", full_path, external=True)


if __name__ == "__main__":
    from nox.__main__ import main

    main()
