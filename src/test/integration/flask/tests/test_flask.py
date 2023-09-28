import unittest
from test.test_utils.span_exporter import wait_for_exporter
from test.test_utils.spans_parser import SpansContainer

import requests


class TestFlaskSpans(unittest.TestCase):
    def test_200_OK(self):
        response = requests.get("http://localhost:5000/")
        response.raise_for_status()

        body = response.json()

        self.assertEqual(body, {"message": "Hello Flask!"})

        wait_for_exporter()

        spans_container = SpansContainer.get_spans_from_file()
        self.assertEqual(1, len(spans_container.spans))

        # assert root
        root = spans_container.get_first_root()
        self.assertIsNotNone(root)
        self.assertEqual(root["kind"], "SpanKind.SERVER")
        self.assertEqual(root["attributes"]["http.status_code"], 200)
        self.assertIsNotNone(root["attributes"]["http.request.headers"])
        self.assertIsNotNone(root["attributes"]["http.response.headers"])
        self.assertEqual(root["attributes"]["http.method"], "GET")
        self.assertEqual(root["attributes"]["http.host"], "localhost:5000")
        self.assertEqual(root["attributes"]["http.route"], "/")

    def test_requests_instrumentation(self):
        response = requests.get("http://localhost:5000/invoke-requests")
        response.raise_for_status()

        body = response.json()

        self.assertIn("https://api.chucknorris.io/jokes/", body["url"])

        wait_for_exporter()

        spans_container = SpansContainer.get_spans_from_file()
        self.assertEqual(2, len(spans_container.spans))

        # assert root
        root = spans_container.get_first_root()
        self.assertIsNotNone(root)
        self.assertEqual(root["kind"], "SpanKind.SERVER")
        self.assertEqual(root["attributes"]["http.status_code"], 200)
        self.assertEqual(root["attributes"]["http.host"], "localhost:5000")
        self.assertEqual(root["attributes"]["http.route"], "/invoke-requests")
        self.assertIsNotNone(root["attributes"]["http.request.headers"])
        self.assertIsNotNone(root["attributes"]["http.response.headers"])

        # assert child spans
        children = spans_container.get_non_internal_children()
        self.assertEqual(1, len(children))
        self.assertEqual(children[0]["attributes"]["http.method"], "GET")
        self.assertEqual(
            children[0]["attributes"]["http.url"],
            "https://api.chucknorris.io/jokes/random",
        )
        self.assertEqual(children[0]["attributes"]["http.status_code"], 200)
        self.assertIsNotNone(children[0]["attributes"]["http.request.headers"])
        self.assertIsNotNone(children[0]["attributes"]["http.response.headers"])
        self.assertIsNotNone(children[0]["attributes"]["http.response.body"])
