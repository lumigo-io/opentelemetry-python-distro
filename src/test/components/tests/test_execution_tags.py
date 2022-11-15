import requests
import time
import unittest

from test.test_utils.spans_parser import SpansContainer


class TestExecutionTags(unittest.TestCase):
    def test_execution_tag(self):
        response = requests.get("http://localhost:8020/invoke-request")
        response.raise_for_status()

        body = response.json()

        assert body is not None

        # TODO Do something deterministic
        time.sleep(3)  # Sleep for two seconds to allow the exporter to catch up

        spans_container = SpansContainer.get_spans_from_file()
        self.assertEqual(4, len(spans_container.spans))

        # assert root
        root = spans_container.get_root()
        self.assertIsNotNone(root)
        root_attributes = root["attributes"]
        self.assertEqual(
            type(root_attributes["lumigo.execution_tags.response_len"]), int
        )
        self.assertEqual(type(root_attributes["lumigo.execution_tags.response"]), str)
        self.assertEqual(root_attributes["lumigo.execution_tags.app"], True)
        self.assertEqual(
            root_attributes["lumigo.execution_tags.app.response"], "success"
        )
        self.assertEqual(root_attributes["lumigo.execution_tags.foo"], ["bar", "baz"])
