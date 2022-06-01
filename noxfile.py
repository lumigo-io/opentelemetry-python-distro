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
def integration_tests_fastapi(session, fastapi_version, uvicorn_version):
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

    with session.chdir("src/test/integration/fastapi"):
        session.install("-r", "requirements_others.txt")

        try:
            session.run(
                "sh",
                "./scripts/start_uvicorn",
                env={
                    "AUTOWRAPT_BOOTSTRAP": "lumigo_opentelemetry",
                    "LUMIGO_DEBUG_SPANDUMP": "./spans.txt",
                    "OTEL_SERVICE_NAME": "app",
                },
                external=True,
            )  # One happy day we will have https://github.com/wntrblm/nox/issues/198

            # TODO Make this deterministic
            # Wait 1s to give time for app to start
            time.sleep(3)

            session.run(
                "pytest",
                "--tb",
                "native",
                "--log-cli-level=INFO",
                "--color=yes",
                "-v",
                "./tests/test_fastapi.py",
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

            session.run("rm", "-f", "./spans.txt", external=True)
