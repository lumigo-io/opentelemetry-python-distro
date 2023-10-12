import os
import subprocess
import sys
from pathlib import Path
from test.test_utils.processes import kill_process


class FastApiSample(object):
    def __init__(self):
        cwd = Path(__file__).parent.parent
        print(f"cwd = {cwd}")
        env = {
            **os.environ,
            "AUTOWRAPT_BOOTSTRAP": "lumigo_opentelemetry",
            "LUMIGO_DEBUG_SPANDUMP": os.environ["LUMIGO_DEBUG_SPANDUMP"],
            "OTEL_SERVICE_NAME": "fastapi_test_app",
        }
        print(f"env = {env}")
        cmd = [sys.executable, "start_uvicorn.py"]
        print(f"cmd = {cmd}")
        self.process = subprocess.Popen(
            cmd,
            cwd=cwd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        is_app_running = False
        for line in self.process.stderr:
            if "Uvicorn running" in str(line):
                print(f"FastApiSample app: {line}")
                is_app_running = True
                break
            print(line)
        if not is_app_running:
            raise Exception("FastApiSample app failed to start")

    def __enter__(self):
        return self

    def __exit__(self, *args):
        # because we need a shell to run uvicorn we need to kill multiple processs,
        # but not the process group because that includes the test process as well
        kill_process("uvicorn")
