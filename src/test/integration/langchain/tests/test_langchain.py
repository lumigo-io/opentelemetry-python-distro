import unittest
from test.test_utils.spans_parser import SpansContainer




class TestLangchainSpans(unittest.TestCase):
    def test_langchain_spans(self):
        spans_container = SpansContainer.parse_spans_from_file()

        self.assertGreaterEqual(len(spans_container.spans), 4)