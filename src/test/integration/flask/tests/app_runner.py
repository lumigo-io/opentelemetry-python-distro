import os
import subprocess
import sys
from pathlib import Path
from test.test_utils.processes import kill_process, wait_for_process_output
from typing import Optional


class FlaskApp(object):
    def __init__(self, port: int, env: Optional[dict] = None):
        self.app = "start_flask.py"
        self.port = port
        cwd = Path(__file__).parent.parent / "app"
        env = {
            **os.environ,
            **(env or {}),
            "AUTOWRAPT_BOOTSTRAP": "lumigo_opentelemetry",
            "OTEL_SERVICE_NAME": "flask_test_app",
            "LUMIGO_DEBUG_SPANDUMP": os.environ["LUMIGO_DEBUG_SPANDUMP"],
        }
        cmd = [
            sys.executable,
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
            wait_for_process_output(self.process, "Running on")
        except Exception as e:
            raise Exception(f"Flask app failed to start on port {self.port}", e)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        kill_process([self.app, str(self.port)])
