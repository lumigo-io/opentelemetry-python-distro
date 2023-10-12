import unittest
from test.test_utils.spans_parser import SpansContainer

import requests

from .app_runner import FastApiSample


class TestFastApiSpans(unittest.TestCase):
    def test_200_OK(self):
        with FastApiSample():
            response = requests.get("http://localhost:8000/")
            response.raise_for_status()

            body = response.json()

            self.assertEqual(body, {"message": "Hello FastAPI!"})

            spans_container = SpansContainer.get_spans_from_file(
                wait_time_sec=10, expected_span_count=3
            )
            self.assertEqual(3, len(spans_container.spans))

            # assert root
            root = spans_container.get_first_root()
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
        with FastApiSample():
            response = requests.get("http://localhost:8000/invoke-requests")
            response.raise_for_status()

            body = response.json()

            self.assertIn("https://api.chucknorris.io/jokes/", body["url"])

            spans_container = SpansContainer.get_spans_from_file(
                wait_time_sec=10, expected_span_count=4
            )
            self.assertEqual(4, len(spans_container.spans))

            # assert root
            root = spans_container.get_first_root()
            self.assertIsNotNone(root)
            self.assertEqual(root["kind"], "SpanKind.SERVER")
            self.assertEqual(root["attributes"]["http.status_code"], 200)
            self.assertIsNotNone(root["attributes"]["http.request.headers"])
            self.assertEqual(
                root["attributes"]["http.url"], "http://127.0.0.1:8000/invoke-requests"
            )

            # assert external request span
            non_internal_children = spans_container.get_non_internal_children()
            self.assertEqual(1, len(non_internal_children))
            external_request_span = non_internal_children[0]
            self.assertEqual(external_request_span["attributes"]["http.method"], "GET")
            self.assertEqual(
                external_request_span["attributes"]["http.url"],
                "https://api.chucknorris.io/jokes/random",
            )
            self.assertEqual(
                external_request_span["attributes"]["http.status_code"], 200
            )

            # assert internal spans
            internals = spans_container.get_internals()
            self.assertEqual(2, len(internals))
            # assert than either of the internal spans have the required attributes
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
            self.assertEqual(
                spans_container.get_attribute_from_list_of_spans(
                    internals, "http.status_code"
                ),
                200,
            )

    def test_large_span_attribute_size_default_max_size(self):
        with FastApiSample():
            response = requests.get(
                "http://localhost:8000/invoke-requests-large-response"
            )
            response.raise_for_status()

            body = response.json()

            assert body is not None

            spans_container = SpansContainer.get_spans_from_file(
                wait_time_sec=10, expected_span_count=4
            )
            self.assertEqual(4, len(spans_container.spans))

            # assert root
            root = spans_container.get_first_root()
            self.assertIsNotNone(root)
            root_attributes = root["attributes"]
            self.assertEqual(root_attributes["http.status_code"], 200)
            self.assertEqual(
                root_attributes["http.url"],
                "http://127.0.0.1:8000/invoke-requests-large-response",
            )
            self.assertEqual(root_attributes["http.method"], "GET")

            # assert external request span
            non_internal_children = spans_container.get_non_internal_children()
            self.assertEqual(1, len(non_internal_children))
            external_request_span = non_internal_children[0]
            self.assertEqual(external_request_span["attributes"]["http.method"], "GET")
            self.assertEqual(
                external_request_span["attributes"]["http.url"],
                "http://universities.hipolabs.com/search?country=United+States",
            )
            self.assertEqual(
                external_request_span["attributes"]["http.status_code"], 200
            )

            # assert internal spans
            internals = spans_container.get_internals()
            self.assertEqual(2, len(internals))
            # assert than either of the internal spans have the required attributes
            self.assertIsNotNone(
                spans_container.get_attribute_from_list_of_spans(
                    internals, "http.response.headers"
                )
            )
            http_response_body_attr = spans_container.get_attribute_from_list_of_spans(
                internals, "http.response.body"
            )
            self.assertIsNotNone(http_response_body_attr)
            self.assertEqual(len(http_response_body_attr), 2048)
            self.assertEqual(
                spans_container.get_attribute_from_list_of_spans(
                    internals, "http.status_code"
                ),
                200,
            )
