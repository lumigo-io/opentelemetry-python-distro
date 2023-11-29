import os
import subprocess
import sys
from pathlib import Path
from test.test_utils.processes import kill_process, wait_for_app_start
from typing import Optional


class DjangoApp(object):
    def __init__(self, app: str, port: int, env: Optional[dict] = None):
        self.app = app
        self.port = port
        cwd = Path(__file__).parent.parent / "app"
        env = {
            **os.environ,
            **(env or {}),
            "OTEL_SERVICE_NAME": "app",
            "LUMIGO_DEBUG_SPANDUMP": os.environ["LUMIGO_DEBUG_SPANDUMP"],
        }
        cmd = [
            sys.executable,
            self.app,
            "runserver",
            str(self.port),
        ]
        self.process = subprocess.Popen(
            cmd,
            cwd=cwd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        # django runs an app that runs an app, so we don't have access to that second
        # app's stdout/stderr, so we can't wait for it to say it's ready
        wait_for_app_start()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        kill_process([self.app, str(self.port)])
