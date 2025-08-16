import sys
import unittest
import httpretty

from unittest import TestCase
from unittest.mock import patch, Mock
from httpretty import HTTPretty

from json import loads
from os import environ

from opentelemetry.sdk.trace import SpanProcessor

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
        # Mock version_info for Python 3.8
        sys.version_info.major = 3
        sys.version_info.minor = 8

        with self.assertLogs("lumigo-opentelemetry", level="WARNING") as cm:
            result = init()

        self.assertEqual(result, {})
        self.assertIn(
            "Unsupported Python version 3.8; only Python 3.9 to 3.13 are supported.",
            cm.output[0],
        )

    @patch("sys.version_info", Mock())
    def test_python_version_supported(self):
        # Mock version_info for Python 3.9
        sys.version_info.major = 3
        sys.version_info.minor = 9

        with self.assertLogs("lumigo-opentelemetry", level="WARNING"):
            result = init()

        self.assertIsInstance(result, dict)

    @patch("sys.version_info", Mock())
    def test_python_version_313_supported(self):
        # Mock version_info for Python 3.13
        sys.version_info.major = 3
        sys.version_info.minor = 13

        with self.assertLogs("lumigo-opentelemetry", level="WARNING"):
            result = init()

        self.assertIsInstance(result, dict)

    @patch("sys.version_info", Mock())
    def test_python_version_too_new(self):
        # Mock version_info for Python 3.14
        sys.version_info.major = 3
        sys.version_info.minor = 14

        with self.assertLogs("lumigo-opentelemetry", level="WARNING") as cm:
            result = init()

        self.assertEqual(result, {})
        self.assertIn(
            "Unsupported Python version 3.14; only Python 3.9 to 3.13 are supported.",
            cm.output[0],
        )


class TestCreateProgrammaticError(unittest.TestCase):
    @httpretty.activate(allow_net_connect=False)
    def test_create_event_with_correct_attributes(self):
        from lumigo_opentelemetry import create_programmatic_error, tracer_provider

        self.assertIsNotNone(create_programmatic_error)

        span_processor = Mock(SpanProcessor)
        tracer_provider.add_span_processor(span_processor)

        tracer = tracer_provider.get_tracer(__name__)
        with tracer.start_as_current_span("Root") as span:
            create_programmatic_error("Error message", "ErrorType")

        # Verify `on_start` was called
        span_processor.on_start.assert_called()

        # Capture the span passed to `on_start`
        span = span_processor.on_start.call_args[0][
            0
        ]  # Extract the `span` argument from the first call

        events = span.events
        # Verify the event was added
        self.assertEqual(len(events), 1)

        event = events[0]
        # Verify the event has the correct attributes
        self.assertEqual(event.name, "Error message")
        self.assertEqual(event.attributes["lumigo.type"], "ErrorType")


class TestLumigoWrapped(unittest.TestCase):
    @httpretty.activate(allow_net_connect=False)
    def test_access_lumigo_wrapped(self):
        from lumigo_opentelemetry import lumigo_wrapped, tracer_provider

        self.assertIsNotNone(lumigo_wrapped)
        self.assertIsNotNone(tracer_provider)

        span_processor = Mock(SpanProcessor)
        tracer_provider.add_span_processor(span_processor)

        @lumigo_wrapped
        def sample_function(x, y):
            return x + y

        result = sample_function(1, 2)

        self.assertEqual(result, 3)

        # Assert `on_start` was called at least once
        span_processor.on_start.assert_called()

        # Verify `on_start` was called
        span_processor.on_start.assert_called()

        # Capture the span passed to `on_start`
        span = span_processor.on_start.call_args[0][
            0
        ]  # Extract the `span` argument from the first call

        # Assess attributes of the span
        self.assertEqual(
            span.attributes["input_args"], "[1, 2]"
        )  # Check serialized input args
        self.assertEqual(
            span.attributes["input_kwargs"], "{}"
        )  # Check serialized input kwargs
        self.assertEqual(
            span.attributes["return_value"], "3"
        )  # Check serialized return value

        tracer = tracer_provider.get_tracer("lumigo")
        assert tracer


class TestLumigoInstrumentLambda(unittest.TestCase):
    @httpretty.activate(allow_net_connect=False)
    def test_access_lumigo_instrument_lambda(self):
        from lumigo_opentelemetry import lumigo_instrument_lambda, tracer_provider

        self.assertIsNotNone(lumigo_instrument_lambda)
        self.assertIsNotNone(tracer_provider)

        span_processor = Mock(SpanProcessor)
        tracer_provider.add_span_processor(span_processor)

        @lumigo_instrument_lambda
        def sample_function(x, y):
            return x + y

        result = sample_function(1, 2)

        self.assertEqual(result, 3)


def test_access_lumigo_id_generator(monkeypatch):
    from lumigo_opentelemetry import tracer_provider

    tracer = tracer_provider.get_tracer("lumigo")
    assert type(tracer.id_generator).__name__ == "LambdaTraceIdGenerator"
    assert tracer.id_generator.generate_trace_id()
    monkeypatch.setenv(
        "_X_AMZN_TRACE_ID",
        "Root=1-688b6f15-89baf8f65f4f119e1f635c3e;Parent=0993133fcbf11ff2;Sampled=0;Lineage=1:9b83d1cd:0",
    )
    assert (
        hex(tracer.id_generator.generate_trace_id())
        == "0x89baf8f65f4f119e1f635c3e00000000"
    )
