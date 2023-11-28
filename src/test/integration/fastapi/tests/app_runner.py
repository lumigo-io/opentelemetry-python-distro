import os
import subprocess
import sys
from pathlib import Path
from test.test_utils.processes import kill_process, wait_for_process_output
from typing import Optional


class FastApiApp(object):
    def __init__(self, app: str, port: int, env: Optional[dict] = None):
        self.app = app
        self.port = port
        cwd = Path(__file__).parent.parent
        env = {
            **os.environ,
            **(env or {}),
            "AUTOWRAPT_BOOTSTRAP": "lumigo_opentelemetry",
            "OTEL_SERVICE_NAME": "fastapi_test_app",
            "LUMIGO_DEBUG_SPANDUMP": os.environ["LUMIGO_DEBUG_SPANDUMP"],
        }
        cmd = [
            sys.executable,
            "start_uvicorn.py",
            "--app",
            self.app,
            "--port",
            str(self.port),
        ]
        self.process = subprocess.Popen(
            cmd,
            cwd=cwd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        try:
            wait_for_process_output(self.process, "Uvicorn running")
        except Exception as e:
            raise Exception(
                f"FastApiApp app '{self.app}' failed to start on port {self.port}", e
            )

    def __enter__(self):
        return self

    def __exit__(self, *args):
        kill_process(["uvicorn", self.app, str(self.port)])
