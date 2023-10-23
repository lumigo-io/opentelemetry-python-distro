import os
import subprocess
import sys
from pathlib import Path
from test.test_utils.processes import kill_process, wait_for_app_start


class GreeterServerApp(object):
    def __init__(self):
        self.app = "greeter_server.py"
        cwd = Path(__file__).parent.parent / "app"
        print(f"cwd = {cwd}")
        env = {
            **os.environ,
            "AUTOWRAPT_BOOTSTRAP": "lumigo_opentelemetry",
            "LUMIGO_DEBUG_SPANDUMP": os.environ["SERVER_SPANDUMP"],
            "OTEL_SERVICE_NAME": "grpcio_test_app",
        }
        print(f"venv bin path = {Path(sys.executable).parent}")
        cmd = [
            sys.executable,
            self.app,
        ]
        print(f"cmd = {cmd}")
        self.process = subprocess.Popen(
            cmd,
            cwd=cwd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        # checking the stderr stream for the "Server started" message breaks the
        # pycharm debugger
        wait_for_app_start()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        # because we need a shell to run uvicorn we need to kill multiple processs,
        # but not the process group because that includes the test process as well
        kill_process(self.app)
