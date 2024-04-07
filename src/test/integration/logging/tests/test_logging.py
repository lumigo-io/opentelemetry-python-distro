import os
import subprocess
import sys
import unittest
from os import path
from test.test_utils.logs_parser import LogsContainer


def run_logging_app():
    sample_path = path.join(
        path.dirname(path.abspath(__file__)),
        "../app/logging_app.py",
    )
    subprocess.check_output(
        [sys.executable, sample_path],
        env={
            **os.environ,
            "AUTOWRAPT_BOOTSTRAP": "lumigo_opentelemetry",
            "OTEL_SERVICE_NAME": "logging-app",
            "LUMIGO_LOGS_ENABLED": "true",
        },
    )


class TestLogging(unittest.TestCase):
    def test_logging(self):
        run_logging_app()

        logs_container = LogsContainer.get_logs_from_file()

        self.assertEqual(len(logs_container), 1)

        logs_container[0]["body"] == "Hello OTEL!"

        # "resource" is currently not a proper dictionary, but a string from a repr(...) call over the resource attributes.
        # Pending a fix in https://github.com/open-telemetry/opentelemetry-python/pull/3346
        logs_container[0]["resource"]["service.name"] == "logging-app"
