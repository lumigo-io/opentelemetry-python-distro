import unittest
from parameterized import parameterized

from test.integration.flask.tests.app_runner import FlaskApp
from test.test_utils.span_exporter import wait_for_exporter
from test.test_utils.spans_parser import SpansContainer

import requests

APP_PORT = 5000


class TestFlaskSpans(unittest.TestCase):
    def test_200_OK(self):
        with FlaskApp(APP_PORT):
            response = requests.get("http://localhost:5000/")
            response.raise_for_status()

            body = response.json()

            self.assertEqual(body, {"message": "Hello Flask!"})

            wait_for_exporter()

            spans_container = SpansContainer.get_spans_from_file()
            self.assertEqual(1, len(spans_container.spans))

            root = spans_container.get_first_root()
            self.assertIsNotNone(root)
            self.assertEqual(root["kind"], "SpanKind.SERVER")
            root_attributes = root["attributes"]
            self.assertEqual(root_attributes["http.status_code"], 200)
            self.assertIsNotNone(root_attributes["http.request.headers"])
            self.assertIsNotNone(root_attributes["http.response.headers"])
            self.assertEqual(root_attributes["http.method"], "GET")
            self.assertEqual(root_attributes["http.host"], "localhost:5000")
            self.assertEqual(root_attributes["http.route"], "/")

    @parameterized.expand(
        [
            ("/", None, None, r'["\/"]', 0),
            ("/", None, None, r'[".*no-match.*"]', 1),
            ("/invoke-requests", None, None, r'[".*no-match.*"]', 2),
            (
                "/invoke-requests",
                None,
                None,
                r'["https:\\/\\/api\\.chucknorris\\.io\\/jokes\\/random"]',
                1,
            ),
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
        with FlaskApp(
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
        with FlaskApp(APP_PORT):
            response = requests.get("http://localhost:5000/invoke-requests")
            response.raise_for_status()

            body = response.json()

            self.assertIn("https://api.chucknorris.io/jokes/", body["url"])

            wait_for_exporter()

            spans_container = SpansContainer.get_spans_from_file()
            self.assertEqual(2, len(spans_container.spans))

            root = spans_container.get_first_root()
            self.assertIsNotNone(root)
            self.assertEqual(root["kind"], "SpanKind.SERVER")
            root_attributes = root["attributes"]
            self.assertEqual(root_attributes["http.status_code"], 200)
            self.assertEqual(root_attributes["http.host"], "localhost:5000")
            self.assertEqual(root_attributes["http.route"], "/invoke-requests")
            self.assertIsNotNone(root_attributes["http.request.headers"])
            self.assertIsNotNone(root_attributes["http.response.headers"])

            children = spans_container.get_non_internal_children()
            self.assertEqual(1, len(children))

            child_span = children[0]
            child_attributes = child_span["attributes"]
            self.assertEqual(child_attributes["http.method"], "GET")
            self.assertEqual(
                child_attributes["http.url"],
                "https://api.chucknorris.io/jokes/random",
            )
            self.assertEqual(child_attributes["http.status_code"], 200)
            self.assertIsNotNone(child_attributes["http.request.headers"])
            self.assertIsNotNone(child_attributes["http.response.headers"])
            self.assertIsNotNone(child_attributes["http.response.body"])
