import requests
import time
import unittest

from test.test_utils.spans_parser import SpansContainer


class TestFastApiSpans(unittest.TestCase):
    def test_large_span_attribute_size_max_size_env_var_was_set(self):
        response = requests.get("http://localhost:8020/invoke-requests-large-response")
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
        self.assertEqual(root_attributes["http.status_code"], 200)

        self.assert_attribute_length(root_attributes, 1)

        # assert child spans
        children = spans_container.get_non_internal_children()
        self.assertEqual(1, len(children))
        child_attributes = children[0]["attributes"]
        self.assert_attribute_length(child_attributes, 1)

    def assert_attribute_length(self, child_attributes: dict, length: int) -> None:
        for k, v in child_attributes.items():
            if type(v) == str:
                assert len(v) == length
