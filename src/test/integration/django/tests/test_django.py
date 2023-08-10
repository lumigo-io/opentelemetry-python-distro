import time
import unittest
from test.test_utils.spans_parser import SpansContainer

import requests


class TestDjangoSpans(unittest.TestCase):
    def test_200_OK(self):
        response = requests.get("http://localhost:8000/")
        response.raise_for_status()

        body = response.json()

        self.assertEqual(body, {"message": "Hello Django!"})

        # TODO Do something deterministic
        time.sleep(3)  # Sleep to allow the exporter to catch up

        spans_container = SpansContainer.get_spans_from_file()
        self.assertEqual(1, len(spans_container.spans))

        # assert root
        root = spans_container.get_root()
        self.assertIsNotNone(root)
        self.assertEqual(root["kind"], "SpanKind.SERVER")
        self.assertEqual(root["attributes"]["http.status_code"], 200)
        self.assertEqual(root["attributes"]["http.method"], "GET")
        self.assertEqual(root["attributes"]["http.host"], "localhost:8000")
        self.assertEqual(root["attributes"]["http.route"], "/")
