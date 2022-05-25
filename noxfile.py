import nox

import os
import time
from typing import List


def python_versions() -> List[str]:
    # On CircleCI, just run the current Python version without
    # creating a venv.
    # In local, try all supported python versions building venvs.
    if os.getenv("CIRCLECI", str(False)).lower() == "true":
        return False

    return ['3.6', '3.7', '3.8', '3.9', '3.10']


def dependency_versions(dependency_name: str) -> List[str]:
    with open(f'src/test/integration/fastapi/supported_versions/{dependency_name}', 'r') as f:
        return [line.strip() for line in f.readlines()]


@nox.session(python=python_versions())
@nox.parametrize('uvicorn_version', dependency_versions('uvicorn'))
@nox.parametrize('fastapi_version', dependency_versions('fastapi'))
def integration_tests_fastapi(session, fastapi_version, uvicorn_version):
    session.run('python3', '--version', external=True)

    session.install(f'uvicorn=={uvicorn_version}')
    session.install(f'fastapi=={fastapi_version}')

    session.install('.')

    with session.chdir('src/test/integration/fastapi'):
        session.install('-r', 'requirements_others.txt')

        try:
            session.run('sh', './scripts/start_uvicorn', external=True)  # One happy day we will have https://github.com/wntrblm/nox/issues/198
            # Wait 1s to give time for app to start
            time.sleep(1)
            session.run('pytest', '--tb', 'native', '--log-cli-level=INFO', '--color=yes', '-v', './tests/test_fastapi.py', env={
                'LUMIGO_DEBUG_SPANDUMP': './spans.txt',
                'OTEL_SERVICE_NAME': 'app',
            })
        finally:
            session.run('pkill', '-9', 'uvicorn', external=True)
            session.run('rm', './spans.txt', external=True)
