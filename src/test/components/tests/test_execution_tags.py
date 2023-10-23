import unittest
from test.test_utils.spans_parser import SpansContainer

import requests

from .app_runner import FastApiApp

APP_PORT = 8020
EXTERNAL_APP_PORT = 8021


class TestExecutionTags(unittest.TestCase):
    def test_execution_tag(self):
        with FastApiApp("app:app", APP_PORT), FastApiApp(
            "fastapi_external_apis.app:app", EXTERNAL_APP_PORT
        ):
            response = requests.get(f"http://localhost:{APP_PORT}/invoke-request")
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
            self.assertEqual(
                type(root_attributes["lumigo.execution_tags.response_len"]), int
            )
            self.assertEqual(
                type(root_attributes["lumigo.execution_tags.response"]), str
            )
            self.assertEqual(root_attributes["lumigo.execution_tags.app"], True)
            self.assertEqual(
                root_attributes["lumigo.execution_tags.app.response"], "success"
            )
            self.assertEqual(
                root_attributes["lumigo.execution_tags.foo"], ["bar", "baz"]
            )
            self.assertEqual(
                root_attributes["lumigo.execution_tags.foo"], ["bar", "baz"]
            )
