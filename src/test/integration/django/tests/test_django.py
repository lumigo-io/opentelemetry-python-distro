import unittest
from test.integration.django.tests.app_runner import DjangoApp
from test.test_utils.span_exporter import wait_for_exporter
from test.test_utils.spans_parser import SpansContainer

import requests

APP_EXECUTABLE = "manage.py"
APP_PORT = 5003


class TestDjangoSpans(unittest.TestCase):
    def test_200_OK(self):
        with DjangoApp(APP_EXECUTABLE, APP_PORT):
            response = requests.get(
                f"http://localhost:{APP_PORT}/", data='{"support": "django"}'
            )
            response.raise_for_status()

            body = response.text

            self.assertIsNotNone(body)

            wait_for_exporter()

            spans_container = SpansContainer.get_spans_from_file()
            self.assertEqual(1, len(spans_container.spans))

            root = spans_container.get_first_root()
            self.assertIsNotNone(root)
            self.assertEqual(root["kind"], "SpanKind.SERVER")
            root_attributes = root["attributes"]
            self.assertEqual(root_attributes["http.status_code"], 200)
            self.assertEqual(
                root_attributes["http.request.body"], '{"support": "django"}'
            )
            self.assertIsNotNone(root_attributes["http.request.headers"])
            self.assertIsNotNone(root_attributes["http.response.headers"])
            self.assertIsNotNone(root_attributes["http.response.body"])
            self.assertEqual(root_attributes["http.method"], "GET")
            self.assertEqual(root_attributes["http.host"], f"localhost:{APP_PORT}")

    def test_endpoint_filter_no_match(self):
        endpoint = f"http://localhost:{APP_PORT}/"
        with DjangoApp(
            APP_EXECUTABLE,
            APP_PORT,
            {"LUMIGO_AUTO_FILTER_HTTP_ENDPOINTS_REGEX": ".*not_matching.*"},
        ):
            response = requests.get(endpoint, data='{"support": "django"}')
            response.raise_for_status()

            body = response.text

            self.assertIsNotNone(body)

            wait_for_exporter()

            spans_container = SpansContainer.get_spans_from_file()
            self.assertEqual(1, len(spans_container.spans))

    def test_endpoint_filter_match(self):
        endpoint = f"http://localhost:{APP_PORT}/"
        with DjangoApp(
            APP_EXECUTABLE,
            APP_PORT,
            {"LUMIGO_AUTO_FILTER_HTTP_ENDPOINTS_REGEX": ".*(localhost|127.0.0.1).*/$"},
        ):
            response = requests.get(endpoint, data='{"support": "django"}')
            response.raise_for_status()
            body = response.text
            self.assertIsNotNone(body)

            wait_for_exporter()

            spans_container = SpansContainer.get_spans_from_file()
            self.assertEqual(0, len(spans_container.spans))
