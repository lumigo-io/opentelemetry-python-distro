import os
import subprocess
import sys
import unittest
from test.test_utils.span_exporter import wait_for_exporter
from test.test_utils.spans_parser import SpansContainer


class TestMotorSpans(unittest.TestCase):
    """
    This package uses pymongo under the hood, so there's no specific instrumentation for it,
        we only want to measure our compatibility with it.
    """

    def test_motor_set_and_get(self):
        sample_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "../app/motor_set_and_get.py",
        )
        subprocess.check_output(
            [sys.executable, sample_path],
            env={
                **os.environ,
                "AUTOWRAPT_BOOTSTRAP": "lumigo_opentelemetry",
                "OTEL_SERVICE_NAME": "motor",
            },
        )

        wait_for_exporter()

        spans = [
            s
            for s in SpansContainer.parse_spans_from_file().spans
            if s["attributes"].get("db.system") == "mongodb"
        ]

        self.assertEqual(len(spans), 3)
        admin_span, set_span, get_span = spans
        self.assertEqual(set_span["attributes"]["db.statement"], "insert")

        self.assertTrue(
            '"my-k": "my-value"' in set_span["attributes"]["db.request.body"]
        )
        self.assertTrue(
            '{"n": 1, "ok": 1.0}' in set_span["attributes"]["db.response.body"]
        )

        self.assertEqual(get_span["attributes"]["db.statement"], "find")
        self.assertTrue(
            '"my-k": "my-value"' in get_span["attributes"]["db.response.body"]
        )
