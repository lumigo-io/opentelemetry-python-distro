import json
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
            "OTEL_SERVICE_NAME": "logging-app",
            "LUMIGO_ENABLE_LOGS": str(logging_enabled).lower(),
            "LUMIGO_DEBUG_LOGDUMP": log_dump_file
            or os.environ.get("LUMIGO_DEBUG_LOGDUMP"),
            "LUMIGO_SECRET_MASKING_REGEX": '[".*super-sekret.*"]',
            # Without this, requiring the lumigo_opentelemetry package will fail in the test app
            "PYTHONPATH": os.environ.get("NOX_SITE_PACKAGES_PATH"),
        },
        capture_output=True,
    )

    try:
        # raise error in case of a non-zero exit code from the process
        completed_process.check_returncode()
        print(completed_process.stdout.decode())
        print(completed_process.stderr.decode())

    except subprocess.CalledProcessError as e:
        print(e.stdout.decode())
        print(e.stderr.decode())
        raise e

    return completed_process.stdout


class TestLogging(unittest.TestCase):
    def test_logging_enabled(self):
        run_logging_app(logging_enabled=True)

        logs = LogsContainer.get_logs_from_file()

        self.assertEqual(len(logs), 2)
        self.assertEqual(
            logs[0]["body"],
            '{"some-thing": "with no recording span", "some-super-sekret-stuff": "****"}',
        )
        self.assertEqual(
            logs[1]["body"],
            '{"some-thing": "with recording span", "some-super-sekret-stuff": "****"}',
        )

        for log in logs:
            self.assertEqual(
                log["resource"]["attributes"]["service.name"], "logging-app"
            )

        self.assertIn("attributes", logs[0])

        # Log with no recording span
        log_attributes = logs[0]["attributes"]
        self.assertEqual(log_attributes["otelSpanID"], "0")
        self.assertEqual(log_attributes["otelTraceID"], "0")
        self.assertEqual(log_attributes["otelServiceName"], "logging-app")
        self.assertEqual(log_attributes["otelTraceSampled"], False)

        # Log with a recording span
        log_attributes = logs[1]["attributes"]
        self.assertEqual(
            log_attributes["otelSpanID"], logs[1]["span_id"].replace("0x", "")
        )
        self.assertEqual(
            log_attributes["otelTraceID"], logs[1]["trace_id"].replace("0x", "")
        )
        self.assertEqual(log_attributes["otelServiceName"], "logging-app")
        self.assertEqual(log_attributes["otelTraceSampled"], True)

    def test_secret_scrubbing_body(self):
        run_logging_app(logging_enabled=True)

        logs = LogsContainer.get_logs_from_file()

        self.assertEqual(len(logs), 2)
        self.assertEqual(
            json.loads(logs[0]["body"]),
            {"some-thing": "with no recording span", "some-super-sekret-stuff": "****"},
        )
        self.assertEqual(
            json.loads(logs[1]["body"]),
            {"some-thing": "with recording span", "some-super-sekret-stuff": "****"},
        )

    def test_logging_disabled(self):
        run_logging_app(logging_enabled=False)

        logs = LogsContainer.get_logs_from_file()

        self.assertEqual(len(logs), 0)

    def test_logging_bad_dump_file(self):
        app_stdout = run_logging_app(
            logging_enabled=True, log_dump_file="\\__0__/.json"
        )

        self.assertTrue(str(app_stdout).find("with recording span") != -1)
