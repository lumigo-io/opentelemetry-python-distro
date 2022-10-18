import requests
import time
import unittest

from test.test_utils.spans_parser import SpansContainer


class TestFastApiSpans(unittest.TestCase):
    def test_200_OK(self):
        response = requests.get("http://localhost:8000/")
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
        self.assertEqual(root["attributes"]["http.url"], "http://127.0.0.1:8000/")

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

    def test_requests_instrumentation(self):
        response = requests.get("http://localhost:8000/invoke-requests")
        response.raise_for_status()

        body = response.json()

        self.assertIn("https://api.chucknorris.io/jokes/", body["url"])

        # TODO Do something deterministic
        time.sleep(3)  # Sleep for two seconds to allow the exporter to catch up

        spans_container = SpansContainer.get_spans_from_file()
        self.assertEqual(4, len(spans_container.spans))

        # assert root
        root = spans_container.get_root()
        self.assertIsNotNone(root)
        self.assertEqual(root["kind"], "SpanKind.SERVER")
        self.assertEqual(root["attributes"]["http.status_code"], 200)
        self.assertEqual(
            root["attributes"]["http.url"], "http://127.0.0.1:8000/invoke-requests"
        )

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

    def test_large_span_attribute_size_default_max_size(self):
        response = requests.get("http://localhost:8000/invoke-requests-large-response")
        response.raise_for_status()

        body = response.json()

        assert body is not None

        # TODO Do something deterministic
        time.sleep(3)  # Sleep for two seconds to allow the exporter to catch up

        spans_container = SpansContainer.get_spans_from_file()
        self.assertGreaterEqual(len(spans_container.spans), 4)

        # assert root
        root = spans_container.get_root()
        self.assertIsNotNone(root)
        root_attributes = root["attributes"]
        self.assertEqual(root_attributes["http.status_code"], 200)
        self.assertEqual(
            root_attributes["http.url"],
            "http://127.0.0.1:8000/invoke-requests-large-response",
        )
        self.assertEqual(root_attributes["http.method"], "GET")

        # assert child spans
        children = spans_container.get_non_internal_children()
        self.assertGreaterEqual(len(children), 1)
        entries_child = list(
            filter(lambda item: "entries" in item["attributes"]["http.url"], children)
        )[0]
        entries_attributes = entries_child["attributes"]
        print("children_attributes")
        print(entries_attributes)
        self.assertEqual(entries_attributes["http.method"], "GET")
        self.assertEqual(
            entries_attributes["http.url"],
            "https://api.publicapis.org/entries",
        )
        self.assertEqual(len(entries_attributes["http.response.body"]), 2048)
        self.assertEqual(entries_attributes["http.status_code"], 200)
        self.assertIsNotNone(entries_attributes["http.request.headers"])
        self.assertIsNotNone(entries_attributes["http.response.headers"])
        self.assertIsNotNone(entries_attributes["http.response.body"])
