import time
import unittest
from test.test_utils.spans_parser import SpansContainer

import requests


class TestFastApiSpans(unittest.TestCase):
    def test_mongo_instrumentation(self):
        response = requests.get("http://localhost:8002/invoke-mongo")

        response.raise_for_status()

        body = response.json()

        self.assertEqual(body, {"status": "ok"})

        # TODO Do something deterministic
        time.sleep(3)  # Sleep to allow the exporter to catch up

        spans_container = SpansContainer.get_spans_from_file()

        # assert mongo children spans
        assert spans_container.find_child_span(
            lambda span: (
                span["kind"] == "SpanKind.CLIENT"
                and span["attributes"]["db.system"] == "mongodb"
                and span["attributes"]["db.name"] == "test"
                and span["attributes"]["db.statement"] == "insert items"
            )
        )

        assert spans_container.find_child_span(
            lambda span: (
                span["kind"] == "SpanKind.CLIENT"
                and span["attributes"]["db.system"] == "mongodb"
                and span["attributes"]["db.name"] == "test"
                and span["attributes"]["db.statement"] == "find items"
            )
        )
