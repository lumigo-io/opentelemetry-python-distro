import os
import subprocess
import sys
import unittest
from os import path
from test.test_utils.logs_parser import LogsContainer


def run_logging_app(logging_enabled: bool):
    app_path = path.join(
        path.dirname(path.abspath(__file__)),
        "../app/logging_app.py",
    )

    subprocess.run(
        [sys.executable, app_path],
        env={
            **os.environ,
            "AUTOWRAPT_BOOTSTRAP": "lumigo_opentelemetry",
            "OTEL_SERVICE_NAME": "logging-app",
            "LUMIGO_LOGS_ENABLED": str(logging_enabled).lower(),
        },
    )


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
