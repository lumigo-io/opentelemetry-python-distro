import unittest
from parameterized import parameterized
from test.test_utils.span_exporter import wait_for_exporter

from test.test_utils.spans_parser import SpansContainer

import requests

from .app_runner import FastApiApp

APP_PORT = 8020
EXTERNAL_APP_PORT = 8021


class TestFastApiSpans(unittest.TestCase):
    def test_200_OK(self):
        with FastApiApp("app:app", APP_PORT):
            response = requests.get(f"http://localhost:{APP_PORT}/")
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
            root_attributes = root["attributes"]
            self.assertEqual(root_attributes["http.status_code"], 200)
            self.assertEqual(root_attributes["http.method"], "GET")
            self.assertEqual(
                root_attributes["http.url"], f"http://127.0.0.1:{APP_PORT}/"
            )

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

    @parameterized.expand(
        [
            ("/", None, None, r'["/"]', 0),
            ("/", None, None, r'[".*no-match.*"]', 3),
            ("/call-external", None, None, r'[".*no-match.*"]', 4),
            ("/call-external", None, None, r'[".*example.*"]', 3),
        ]
    )
    def test_endpoint_filter_match(
        self,
        endpoint,
        server_regexes,
        client_regexes,
        general_regexes,
        expected_span_count,
    ):
        endpoint = f"http://localhost:{APP_PORT}{endpoint}"
        with FastApiApp(
            "app:app",
            APP_PORT,
            {
                "LUMIGO_FILTER_HTTP_ENDPOINTS_REGEX_SERVER": server_regexes or "",
                "LUMIGO_FILTER_HTTP_ENDPOINTS_REGEX_CLIENT": client_regexes or "",
                "LUMIGO_FILTER_HTTP_ENDPOINTS_REGEX": general_regexes or "",
            },
        ):
            response = requests.get(endpoint)
            response.raise_for_status()

            wait_for_exporter()

            spans_container = SpansContainer.get_spans_from_file()
            self.assertEqual(expected_span_count, len(spans_container.spans))

    def test_requests_instrumentation(self):
        with FastApiApp("app:app", APP_PORT):
            response = requests.post(
                f"http://localhost:{APP_PORT}/invoke-requests", json={"a": "b"}
            )
            response.raise_for_status()
            body = response.json()
            expected_url = "http://sheker.kol.shehoo:8021/little-response"
            self.assertIn(expected_url, body["url"])

            spans_container = SpansContainer.get_spans_from_file(
                wait_time_sec=10, expected_span_count=5
            )
            self.assertEqual(5, len(spans_container.spans))

            # assert root
            root = spans_container.get_first_root()
            self.assertIsNotNone(root)
            self.assertEqual(root["kind"], "SpanKind.SERVER")
            root_attributes = root["attributes"]
            self.assertEqual(root_attributes["http.status_code"], 200)
            self.assertIsNotNone(root_attributes["http.request.headers"])
            self.assertEqual(
                root_attributes["http.url"],
                f"http://127.0.0.1:{APP_PORT}/invoke-requests",
            )

            # assert internal spans
            internals = spans_container.get_internals()
            self.assertEqual(4, len(internals))
            # assert than either of the internal spans have the required attributes
            self.assertIsNotNone(
                spans_container.get_attribute_from_list_of_spans(
                    internals, "http.request.body"
                )
            )
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
        with FastApiApp("app:app", APP_PORT):
            response = requests.get(
                f"http://localhost:{APP_PORT}/invoke-requests-large-response"
            )
            response.raise_for_status()
            body = response.json()
            assert body is not None

            spans_container = SpansContainer.get_spans_from_file(
                wait_time_sec=10, expected_span_count=3
            )
            self.assertEqual(3, len(spans_container.spans))

            # assert root
            root = spans_container.get_first_root()
            self.assertIsNotNone(root)
            root_attributes = root["attributes"]
            self.assertEqual(root_attributes["http.status_code"], 200)
            self.assertEqual(
                root_attributes["http.url"],
                f"http://127.0.0.1:{APP_PORT}/invoke-requests-large-response",
            )
            self.assertEqual(root_attributes["http.method"], "GET")

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
