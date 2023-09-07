import unittest
from test.test_utils.span_exporter import wait_for_exporter
from test.test_utils.spans_parser import SpansContainer

import requests


class TestFastApiSpans(unittest.TestCase):
    def test_pymysql_instrumentation(self):
        response = requests.get("http://localhost:8003/invoke-pymysql")

        response.raise_for_status()

        body = response.json()

        self.assertEqual(body, {"status": "ok"})

        wait_for_exporter()

        spans_container = SpansContainer.get_spans_from_file()

        # assert mongo children spans
        children = spans_container.get_non_internal_children(name_filter="SELECT")
        self.assertGreaterEqual(len(children), 1)
        self.assertEqual(children[0]["attributes"]["db.system"], "mysql")
        self.assertEqual(children[0]["attributes"]["db.statement"], "SELECT VERSION()")
