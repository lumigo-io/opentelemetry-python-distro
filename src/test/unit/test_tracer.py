import sys
import unittest
import httpretty

from unittest import TestCase
from unittest.mock import patch, Mock
from httpretty import HTTPretty

from json import loads
from os import environ

from lumigo_opentelemetry import init


class TestDistroInit(unittest.TestCase):
    def test_access_trace_and_logging_providers(self):
        from lumigo_opentelemetry import tracer_provider, logger_provider

        self.assertIsNotNone(tracer_provider)
        self.assertTrue(hasattr(tracer_provider, "force_flush"))
        self.assertTrue(hasattr(tracer_provider, "shutdown"))

        self.assertIsNotNone(logger_provider)
        self.assertTrue(hasattr(logger_provider, "force_flush"))
        self.assertTrue(hasattr(logger_provider, "shutdown"))


class TestDependencyReport(TestCase):
    @httpretty.activate(allow_net_connect=False)
    @patch.dict(
        environ, {"LUMIGO_TRACER_TOKEN": "", "LUMIGO_REPORT_DEPENDENCIES": "true"}
    )
    def test_dependency_report_disabled_if_no_lumigo_token(self):
        assert not environ.get("LUMIGO_TRACER_TOKEN")

        init()

        assert not httpretty.latest_requests()

    @httpretty.activate(allow_net_connect=False)
    @patch.dict(
        environ,
        {"LUMIGO_TRACER_TOKEN": "abcdef", "LUMIGO_REPORT_DEPENDENCIES": "false"},
    )
    def test_dependency_report_disabled_if_lumigo_report_dependencies_false(self):
        init()

        assert not httpretty.latest_requests()

    @httpretty.activate(allow_net_connect=False)
    @patch.dict(
        environ, {"LUMIGO_TRACER_TOKEN": "abcdef", "LUMIGO_REPORT_DEPENDENCIES": "true"}
    )
    def test_dependency_report_fails(self):
        httpretty.register_uri(
            HTTPretty.POST,
            "https://ga-otlp.lumigo-tracer-edge.golumigo.com/v1/dependencies",
            headers={"Authentication": "LumigoToken abcdef"},
            status_code=500,
        )

        init()

        # Check we did call the endpoint, it failed, and init() didn't
        assert httpretty.latest_requests()

    @httpretty.activate(allow_net_connect=False)
    @patch.dict(
        environ,
        {
            "LUMIGO_TRACER_TOKEN": "abcdef",
            "LUMIGO_REPORT_DEPENDENCIES": "true",
            "LUMIGO_ENDPOINT": "https://some.url",
        },
    )
    def test_dependency_report_enabled_if_lumigo_endpoint_not_default(self):
        self._test_dependency_report_called()

    @httpretty.activate(allow_net_connect=False)
    @patch.dict(
        environ, {"LUMIGO_TRACER_TOKEN": "abcdef", "LUMIGO_REPORT_DEPENDENCIES": "true"}
    )
    def test_dependency_report_called(self):
        self._test_dependency_report_called()

    def _test_dependency_report_called(self):
        httpretty.register_uri(
            HTTPretty.POST,
            "https://ga-otlp.lumigo-tracer-edge.golumigo.com/v1/dependencies",
            headers={"Authentication": "LumigoToken abcdef"},
            status_code=200,
        )

        init()

        # TODO because of the autoload mechanics, that assume that init()
        # is only called implicitly on import, here technically we execute
        # init twice, and we check only the latest request.
        data = loads(httpretty.last_request().body)

        resource_attributes = data["resourceAttributes"]
        dependencies = data["dependencies"]

        assert resource_attributes and resource_attributes["lumigo.distro.version"]
        assert "process.environ" not in resource_attributes.keys()
        assert dependencies


class TestPythonVersionCheck(TestCase):
    @patch("sys.version_info", Mock())
    def test_python_version_too_old(self):
        # Mock version_info for Python 3.7
        sys.version_info.major = 3
        sys.version_info.minor = 7

        with self.assertLogs("lumigo-opentelemetry", level="WARNING") as cm:
            result = init()

        self.assertEqual(result, {})
        self.assertIn(
            "Unsupported Python version 3.7; only Python 3.8 to 3.11 are supported.",
            cm.output[0],
        )

    @patch("sys.version_info", Mock())
    def test_python_version_supported(self):
        # Mock version_info for Python 3.8
        sys.version_info.major = 3
        sys.version_info.minor = 8

        with self.assertLogs("lumigo-opentelemetry", level="WARNING"):
            result = init()

        self.assertIsInstance(result, dict)

    @patch("sys.version_info", Mock())
    def test_python_version_too_new(self):
        # Mock version_info for Python 3.12
        sys.version_info.major = 3
        sys.version_info.minor = 12

        with self.assertLogs("lumigo-opentelemetry", level="WARNING") as cm:
            result = init()

        self.assertEqual(result, {})
        self.assertIn(
            "Unsupported Python version 3.12; only Python 3.8 to 3.11 are supported.",
            cm.output[0],
        )
