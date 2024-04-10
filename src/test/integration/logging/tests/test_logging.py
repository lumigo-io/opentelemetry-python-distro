import os
import subprocess
import sys
import unittest
from os import path

from test.test_utils.logs_parser import LogsContainer


def run_logging_app(logging_enabled: bool, log_dump_file: str = None):
    app_path = path.join(
        path.dirname(path.abspath(__file__)),
        "../app/logging_app.py",
    )

    completed_process = subprocess.run(
        [sys.executable, app_path],
        env={
            **os.environ,
            "AUTOWRAPT_BOOTSTRAP": "lumigo_opentelemetry",
            "OTEL_SERVICE_NAME": "logging-app",
            "LUMIGO_LOGS_ENABLED": str(logging_enabled).lower(),
            "LUMIGO_DEBUG_LOGDUMP": log_dump_file
            or os.environ.get("LUMIGO_DEBUG_LOGDUMP"),
        },
        capture_output=True,
    )

    # raise error in case of a non-zero exit code from the process
    completed_process.check_returncode()

    return completed_process.stdout


class TestLogging(unittest.TestCase):
    def test_logging_enabled(self):
        run_logging_app(logging_enabled=True)

        logs_container = LogsContainer.get_logs_from_file()

        self.assertEqual(len(logs_container), 1)
        self.assertEqual(logs_container[0]["body"], "Hello OTEL!")

        # "resource" is currently not a proper dictionary, but a string from a repr(...) call over the resource attributes.
        # Pending a fix in https://github.com/open-telemetry/opentelemetry-python/pull/3346
        self.assertIn("'service.name': 'logging-app'", logs_container[0]["resource"])
        # self.assertEqual(logs_container[0]["resource"]["service.name"], "logging-app")

        self.assertIn("attributes", logs_container[0])

        log_attributes = logs_container[0]["attributes"]
        self.assertEqual(
            log_attributes["otelSpanID"], logs_container[0]["span_id"].replace("0x", "")
        )
        self.assertEqual(
            log_attributes["otelTraceID"],
            logs_container[0]["trace_id"].replace("0x", ""),
        )
        self.assertEqual(log_attributes["otelServiceName"], "logging-app")
        self.assertEqual(log_attributes["otelTraceSampled"], True)

    def test_logging_disabled(self):
        run_logging_app(logging_enabled=False)

        logs_container = LogsContainer.get_logs_from_file()

        self.assertEqual(len(logs_container), 0)

    def test_logging_bad_dump_file(self):
        app_stdout = run_logging_app(
            logging_enabled=True, log_dump_file="\\__0__/.json"
        )

        self.assertTrue(str(app_stdout).find('"body": "Hello OTEL!"') != -1)
