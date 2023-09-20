import unittest
from test.test_utils.span_exporter import wait_for_exporter
from test.test_utils.spans_parser import SpansContainer

import requests


class TestDjangoSpans(unittest.TestCase):
    def test_200_OK(self):
        response = requests.get("http://localhost:5003/", data='{"support": "django"}')
        response.raise_for_status()

        body = response.text

        self.assertIsNotNone(body)

        wait_for_exporter()

        spans_container = SpansContainer.get_spans_from_file()
        self.assertEqual(1, len(spans_container.spans))

        # assert root
        root = spans_container.get_root()
        self.assertIsNotNone(root)
        self.assertEqual(root["kind"], "SpanKind.SERVER")
        self.assertEqual(root["attributes"]["http.status_code"], 200)
        self.assertEqual(
            root["attributes"]["http.request.body"], '{"support": "django"}'
        )
        self.assertIsNotNone(root["attributes"]["http.request.headers"])
        self.assertIsNotNone(root["attributes"]["http.response.headers"])
        self.assertIsNotNone(root["attributes"]["http.response.body"])
        self.assertEqual(root["attributes"]["http.method"], "GET")
        self.assertEqual(root["attributes"]["http.host"], "localhost:5003")
