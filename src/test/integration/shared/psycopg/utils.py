import os
import subprocess
import sys
from os import path


def run_psycopg_sample(
    sample_name: str,
    connection_url: str,
    test_name: str,
    test_email: str,
    module_under_testing: str,
):
    sample_path = path.join(
        path.dirname(path.abspath(__file__)),
        f"./psycopg_{sample_name}.py",
    )
    subprocess.check_output(
        [sys.executable, sample_path],
        env={
            **os.environ,
            "CONNECTION_URL": connection_url,
            "TEST_NAME": test_name,
            "TEST_EMAIL": test_email,
            "AUTOWRAPT_BOOTSTRAP": "lumigo_opentelemetry",
            "OTEL_SERVICE_NAME": f"psycopg_{sample_name}-app",
            "MODULE_UNDER_TESTING": module_under_testing,
        },
    )
