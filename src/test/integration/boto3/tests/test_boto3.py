import requests
import time
import unittest

from test.test_utils.spans_parser import SpansContainer


class TestFastApiSpans(unittest.TestCase):
    def test_200_OK(self):
        response = requests.get("http://localhost:8001/")
        response.raise_for_status()

        body = response.json()

        self.assertEqual(body, {"message": "Hello FastAPI!"})

        # TODO Do something deterministic
        time.sleep(3)  # Sleep for two seconds to allow the exporter to catch up

        spans_container = SpansContainer.get_spans_from_file()
        self.assertEqual(3, len(spans_container.spans))

        # assert root
        root = spans_container.get_root()
        self.assertIsNotNone(root)
        self.assertEqual(root["kind"], "SpanKind.SERVER")
        self.assertEqual(root["attributes"]["http.status_code"], 200)
        self.assertEqual(root["attributes"]["http.method"], "GET")
        self.assertEqual(root["attributes"]["http.url"], "http://127.0.0.1:8001/")

        # assert internal spans
        internals = spans_container.get_internals()
        self.assertEqual(2, len(internals))
        self.assertIsNotNone(
            spans_container.get_attribute_from_list_of_spans(
                internals, "http.response.headers"
            )
        )
        self.assertIsNotNone(
            spans_container.get_attribute_from_list_of_spans(
                internals, "http.response.body"
            )
        )

    def test_boto3_instrumentation(self):
        response = requests.post("http://localhost:8001/invoke-boto3")

        response.raise_for_status()

        body = response.json()

        self.assertEqual(body, {"status": "ok"})

        # TODO Do something deterministic
        time.sleep(3)  # Sleep for two seconds to allow the exporter to catch up

        spans_container = SpansContainer.get_spans_from_file()
        self.assertEqual(4, len(spans_container.spans))

        # assert root
        root = spans_container.get_root()
        self.assertEqual(root["attributes"]["http.method"], "POST")

        # assert child spans
        children = spans_container.get_non_internal_children()
        self.assertEqual(1, len(children))
        self.assertIsNotNone(children[0]["attributes"]["aws.service"])
        self.assertIsNotNone(children[0]["attributes"]["aws.region"])
        self.assertIsNotNone(children[0]["attributes"]["rpc.method"])
        self.assertIsNotNone(children[0]["attributes"]["http.status_code"])
