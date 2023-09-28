import unittest
from test.test_utils.span_exporter import wait_for_exporter
from test.test_utils.spans_parser import SpansContainer

import requests


class TestPyMongoSpans(unittest.TestCase):
    def test_mongo_instrumentation(self):
        response = requests.get("http://localhost:8002/invoke-mongo")

        response.raise_for_status()

        body = response.json()

        self.assertEqual(body, {"status": "ok"})

        wait_for_exporter()

        spans = [
            s
            for s in SpansContainer.parse_spans_from_file().spans
            if s["attributes"].get("db.system") == "mongodb"
        ]

        set_span, get_span = spans[
            -2:
        ]  # there are more spans to connect to the mongo container

        # assert mongo children spans
        assert (
            set_span["kind"] == "SpanKind.CLIENT"
            and set_span["attributes"]["db.system"] == "mongodb"
            and set_span["attributes"]["db.name"] == "test"
            and set_span["attributes"]["db.statement"] == "insert"
            and '"street": "2 Avenue"' in set_span["attributes"]["db.request.body"]
            and '{"n": 1, "ok": 1.0}' in set_span["attributes"]["db.response.body"]
        )

        assert (
            get_span["kind"] == "SpanKind.CLIENT"
            and get_span["attributes"]["db.system"] == "mongodb"
            and get_span["attributes"]["db.name"] == "test"
            and get_span["attributes"]["db.statement"] == "find"
            and '"street": "2 Avenue"' in get_span["attributes"]["db.response.body"]
        )
