import json

import requests
import time
import unittest

from test.test_utils.spans_parser import SpansContainer


class TestFastApiSpans(unittest.TestCase):
    def assert_is_version(self, version: str):
        major, minor, patch = version.split(".")
        self.assertTrue(major.isdigit())
        self.assertTrue(minor.isdigit())
        self.assertTrue(patch.isdigit())

    def assert_have_env_vars(self, root: dict):
        collected_envs: str = root["resource"]["process.environ"]
        self.assertTrue(isinstance(collected_envs, str))
        self.assertGreaterEqual(len(collected_envs), 1)
        self.assertTrue(
            collected_envs.endswith("...[too long]") or json.loads(collected_envs)
        )

    def assert_otel_detector(self, root: dict):
        self.assertEqual(root["resource"]["K0"], "V0")
        self.assertEqual(root["resource"]["K1"], "V1")
        self.assertEqual(root["resource"]["service.name"], "app")

    def test_boto3_instrumentation(self):
        response = requests.post("http://localhost:8001/invoke-boto3")

        response.raise_for_status()

        body = response.json()

        self.assertEqual(body, {"status": "ok"})

        # TODO Do something deterministic
        time.sleep(3)  # Sleep for two seconds to allow the exporter to catch up

        spans_container = SpansContainer.get_spans_from_file()
        self.assertEqual(4, len(spans_container.spans))

        # assert root
        root = spans_container.get_root()
        self.assertEqual(root["attributes"]["http.method"], "POST")
        self.assertEqual(root["resource"]["process.runtime.name"], "cpython")
        self.assertTrue(root["resource"]["process.runtime.version"].startswith("3."))
        self.assert_is_version(root["resource"]["process.runtime.version"])
        self.assert_is_version(root["resource"]["lumigo.distro.version"])
        self.assert_have_env_vars(root)
        self.assert_otel_detector(root)

        # assert child spans
        children = spans_container.get_non_internal_children()
        self.assertEqual(1, len(children))
        self.assertIsNotNone(children[0]["attributes"]["aws.service"])
        self.assertIsNotNone(children[0]["attributes"]["aws.region"])
        self.assertIsNotNone(children[0]["attributes"]["rpc.method"])
        self.assertIsNotNone(children[0]["attributes"]["http.status_code"])
