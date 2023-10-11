import os
import subprocess
import sys
import unittest
from pathlib import Path
from test.test_utils.processes import kill_process
from test.test_utils.span_exporter import wait_for_exporter
from test.test_utils.spans_parser import SpansContainer

import requests


class FastApiSample(object):
    def __init__(self):
        cwd = Path(__file__).parent.parent
        print(f"cwd = {cwd}")
        env = {
            **os.environ,
            "AUTOWRAPT_BOOTSTRAP": "lumigo_opentelemetry",
            "LUMIGO_DEBUG_SPANDUMP": os.environ["LUMIGO_DEBUG_SPANDUMP"],
            "OTEL_SERVICE_NAME": "fastapi_test_app",
        }
        print(f"env = {env}")
        venv_bin_path = Path(sys.executable).parent
        print(f"venv_bin_path = {venv_bin_path}")
        cmd = f". {venv_bin_path}/activate; uvicorn app:app --port 8000"
        print(f"cmd = {cmd}")
        self.process = subprocess.Popen(
            cmd,
            cwd=cwd,
            env=env,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        is_app_running = False
        for line in self.process.stderr:
            if "Uvicorn running" in str(line):
                print(f"FastApiSample app: {line}")
                is_app_running = True
                break
            print(line)
        if not is_app_running:
            raise Exception("FastApiSample app failed to start")

    def __enter__(self):
        return self

    def __exit__(self, *args):
        # because we need a shell to run uvicorn we need to kill multiple processs,
        # but not the process group because that includes the test process as well
        kill_process("uvicorn")


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

            wait_for_exporter()

            spans_container = SpansContainer.get_spans_from_file()
            self.assertEqual(4, len(spans_container.spans))

            # assert root
            root = spans_container.get_first_root()
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
        with FastApiSample():
            response = requests.get(
                "http://localhost:8000/invoke-requests-large-response"
            )
            response.raise_for_status()

            body = response.json()

            assert body is not None

            wait_for_exporter()

            spans_container = SpansContainer.get_spans_from_file()
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

            # assert child spans
            children = spans_container.get_non_internal_children()
            self.assertEqual(1, len(children))
            children_attributes = children[0]["attributes"]
            self.assertEqual(children_attributes["http.method"], "GET")
            self.assertEqual(
                children_attributes["http.url"],
                "http://universities.hipolabs.com/search?country=United+States",
            )

            self.assertEqual(len(children_attributes["http.response.body"]), 2048)
            self.assertEqual(children_attributes["http.status_code"], 200)
            self.assertIsNotNone(children_attributes["http.request.headers"])
            self.assertIsNotNone(children_attributes["http.response.headers"])
            self.assertIsNotNone(children_attributes["http.response.body"])
