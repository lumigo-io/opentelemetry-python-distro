import tempfile

import nox

import os
import time
from typing import List, Union


def python_versions() -> Union[List[str], bool]:
    # On CircleCI, just run the current Python version without
    # creating a venv.
    # In local, try all supported python versions building venvs.
    if os.getenv("CIRCLECI", str(False)).lower() == "true":
        return False

    return ["3.6", "3.7", "3.8", "3.9", "3.10"]


def dependency_versions(dependency_name: str) -> List[str]:
    with open(
        f"src/test/integration/fastapi/supported_versions/{dependency_name}", "r"
    ) as f:
        return [line.strip() for line in f.readlines()]


@nox.session(python=python_versions())
@nox.parametrize("uvicorn_version", dependency_versions("uvicorn"))
@nox.parametrize("fastapi_version", dependency_versions("fastapi"))
@nox.parametrize("boto3_version", dependency_versions("boto3"))
# @nox.parametrize("pymongo_version", dependency_versions("pymongo"))
# @nox.parametrize("pymysql_version", dependency_versions("pymysql"))
def integration_tests_fastapi(
    session,
    fastapi_version,
    uvicorn_version,
    boto3_version,
    # pymongo_version,
    # pymysql_version,
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
    try:
        session.install(f"boto3=={boto3_version}")
    except:  # noqa
        session.log("Cannot install 'boto3' version '%s'", boto3_version)
        return
    # try:
    #     session.install(f"pymongo=={pymongo_version}")
    # except:  # noqa
    #     session.log("Cannot install 'pymongo' version '%s'", pymongo_version)
    #     return
    # try:
    #     session.install(f"PyMySQL=={pymysql_version}")
    # except:  # noqa
    #     session.log("Cannot install 'PyMySQL' version '%s'", pymysql_version)
    #     return

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
