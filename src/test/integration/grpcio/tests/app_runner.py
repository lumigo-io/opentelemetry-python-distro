import os
import subprocess
import sys
from pathlib import Path
from test.test_utils.processes import kill_process, wait_for_process_output


class GreeterServerApp(object):
    def __init__(self):
        self.app = "greeter_server.py"
        cwd = Path(__file__).parent.parent / "app"
        env = {
            **os.environ,
            "AUTOWRAPT_BOOTSTRAP": "lumigo_opentelemetry",
            "LUMIGO_DEBUG_SPANDUMP": os.environ["SERVER_SPANDUMP"],
            "OTEL_SERVICE_NAME": "grpcio_test_app",
        }
        cmd = [
            sys.executable,
            self.app,
        ]
        self.process = subprocess.Popen(
            cmd,
            cwd=cwd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        try:
            wait_for_process_output(self.process, "Server started", timeout=15)
        except Exception as e:
            raise Exception(f"GreeterServer app '{self.app}' failed to start", e)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        kill_process(self.app)
