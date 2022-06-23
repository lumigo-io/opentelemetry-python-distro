import tempfile

import nox

import os
import time
from typing import List, Union


def python_versions() -> Union[List[str], bool]:
    # On Github, just run the current Python version without
    # creating a venv.
    # In local, try all supported python versions building venvs.
    if os.getenv("CI", str(False)).lower() == "true":
        return False

    return ["3.7", "3.8", "3.9", "3.10"]


def dependency_versions(directory: str, dependency_name: str) -> List[str]:
    """Dependenciy versions are listed in the 'tested_versions/<dependency_name>' files of the instrumentation
    packages, and symlinked under the relevant integration tests."""
    try:
        with open(
            os.path.dirname(__file__)
            + f"/src/test/integration/{directory}/tested_versions/{dependency_name}",
            "r",
        ) as f:
            return [
                line.strip()
                for line in f.readlines()
                if line.strip()[0] != "!"  # We mark incompatible versions with '1'
            ]
    except FileNotFoundError:
        return []


@nox.session(python=python_versions())
@nox.parametrize(
    "boto3_version", dependency_versions(directory="boto3", dependency_name="boto3")
)
def integration_tests_boto3(
    session,
    boto3_version,
):
    try:
        session.install(f"boto3=={boto3_version}")
    except:  # noqa
        session.log("Cannot install 'boto3' version '%s'", boto3_version)
        return

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
    "uvicorn_version",
    dependency_versions(directory="fastapi", dependency_name="uvicorn"),
)
@nox.parametrize(
    "fastapi_version",
    dependency_versions(directory="fastapi", dependency_name="fastapi"),
)
def integration_tests_fastapi(
    session,
    fastapi_version,
    uvicorn_version,
):
    try:
        session.install(f"uvicorn=={uvicorn_version}")
    except:  # noqa
        session.log("Cannot install 'uvicorn' version '%s'", uvicorn_version)
        return

    try:
        session.install(f"fastapi=={fastapi_version}")
    except:  # noqa
        session.log("Cannot install 'uvicorn' version '%s'", uvicorn_version)
        return

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
    "flask_version", dependency_versions(directory="flask", dependency_name="flask")
)
def integration_tests_flask(session, flask_version):
    try:
        session.install(f"flask=={flask_version}")
    except:  # noqa
        session.log("Cannot install 'flask' version '%s'", flask_version)
        return

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
    dependency_versions(directory="pymongo", dependency_name="pymongo"),
)
def integration_tests_pymongo(
    session,
    pymongo_version,
):
    try:
        session.install(f"pymongo=={pymongo_version}")
    except:  # noqa
        session.log("Cannot install 'pymongo' version '%s'", pymongo_version)
        return

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
    dependency_versions(directory="pymysql", dependency_name="pymysql"),
)
def integration_tests_pymysql(
    session,
    pymysql_version,
):
    try:
        session.install(f"PyMySQL=={pymysql_version}")
    except:  # noqa
        session.log("Cannot install 'PyMySQL' version '%s'", pymysql_version)
        return

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
