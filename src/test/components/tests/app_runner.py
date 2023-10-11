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
        venv_bin_path = Path(sys.executable).parent
        print(f"venv_bin_path = {venv_bin_path}")
        cmd = (
            f". {venv_bin_path}/activate;"
            "uvicorn fastapi_external_apis.app:app --port 8021 &"
            "uvicorn app:app --port 8020 &"
        )
        print(f"cmd = {cmd}")
        self.process = subprocess.Popen(
            cmd,
            cwd=cwd,
            env=env,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        is_app_running = False
        for line in self.process.stderr:
            print(line)
            if "Uvicorn running" in str(line):
                is_app_running = True
                break
        if not is_app_running:
            raise Exception("FastApiSample app failed to start")

    def __enter__(self):
        return self

    def __exit__(self, *args):
        # because we need a shell to run uvicorn we need to kill multiple processs,
        # but not the process group because that includes the test process as well
        kill_process("uvicorn")
