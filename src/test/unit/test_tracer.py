import os
import sys
import unittest
import httpretty
import pytest

from unittest import TestCase
from unittest.mock import patch, Mock
from httpretty import HTTPretty

from json import loads
from os import environ

from opentelemetry.sdk.trace import SpanProcessor

from lumigo_opentelemetry import init, USING_DEFAULT_TIMEOUT_MESSAGE


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


class MockLambdaContext:
    """Mock Lambda context for testing"""

    def __init__(self, remaining_time_ms=5000):
        self._remaining_time_ms = remaining_time_ms

    def get_remaining_time_in_millis(self):
        return self._remaining_time_ms


class MockLambdaContextWithException:
    """Mock Lambda context that raises exception when accessing get_remaining_time_in_millis"""

    def get_remaining_time_in_millis(self):
        raise RuntimeError("Failed to get remaining time")


class MockContextWithoutMethod:
    """Mock context without get_remaining_time_in_millis method"""

    pass


class TestForceFlushWithDynamicTimeout(unittest.TestCase):
    def setUp(self):
        self.tracer_provider_patcher = patch("opentelemetry.trace.get_tracer_provider")
        self.mock_tracer_provider = Mock()
        self.mock_tracer_provider_getter = self.tracer_provider_patcher.start()
        self.mock_tracer_provider_getter.return_value = self.mock_tracer_provider

        self.logger_patcher = patch("lumigo_opentelemetry.logger")
        self.mock_logger = self.logger_patcher.start()

    def tearDown(self):
        self.tracer_provider_patcher.stop()
        self.logger_patcher.stop()

    def test_flush_with_lambda_context_happy_flow(self):
        """Test successful flush with Lambda context"""
        from lumigo_opentelemetry import _flush_with_timeout

        context = MockLambdaContext(remaining_time_ms=5000)
        args = ["event", context]

        _flush_with_timeout(args)

        # Should calculate dynamic timeout: (5000 - 500) / 1000 = 4.5 seconds = 4500ms
        self.mock_tracer_provider.force_flush.assert_called_once_with(
            timeout_millis=4500
        )
        self.mock_logger.debug.assert_called_with(
            "Lambda remaining time: 5000ms, calculated flush timeout: 4.5s"
        )

    def test_flush_with_low_remaining_time_direct_calculation(self):
        """Test direct calculation for low remaining time scenarios"""
        from lumigo_opentelemetry import _flush_with_timeout

        context = MockLambdaContext(remaining_time_ms=800)  # Low remaining time
        args = ["event", context]

        _flush_with_timeout(args)

        # Should use calculated timeout directly: (800 - 80) / 1000 = 0.72s = 720ms
        self.mock_tracer_provider.force_flush.assert_called_once_with(
            timeout_millis=720
        )
        self.mock_logger.debug.assert_called_with(
            "Lambda remaining time: 800ms, calculated flush timeout: 0.72s"
        )

    def test_flush_with_very_low_remaining_time_direct_calculation(self):
        """Test direct calculation for very low remaining time"""
        from lumigo_opentelemetry import _flush_with_timeout

        context = MockLambdaContext(remaining_time_ms=100)  # Very low remaining time
        args = ["event", context]

        _flush_with_timeout(args)

        # Should use calculated timeout directly: (100 - 10) / 1000 = 0.09s = 90ms
        self.mock_tracer_provider.force_flush.assert_called_once_with(timeout_millis=90)
        self.mock_logger.debug.assert_called_with(
            "Lambda remaining time: 100ms, calculated flush timeout: 0.09s"
        )

    def test_flush_without_lambda_context(self):
        """Test flush when no Lambda context is provided"""
        from lumigo_opentelemetry import _flush_with_timeout

        args = ["single_arg"]  # Insufficient args

        _flush_with_timeout(args)

        # Should use default 1-second timeout
        self.mock_tracer_provider.force_flush.assert_called_once_with(
            timeout_millis=1000
        )
        self.mock_logger.debug.assert_called_with(
            f"Context does not have get_remaining_time_in_millis method or insufficient args. {USING_DEFAULT_TIMEOUT_MESSAGE}"
        )

    def test_flush_with_context_without_method(self):
        """Test flush when context doesn't have get_remaining_time_in_millis method"""
        from lumigo_opentelemetry import _flush_with_timeout

        context = MockContextWithoutMethod()
        args = ["event", context]

        _flush_with_timeout(args)

        # Should use default 1-second timeout
        self.mock_tracer_provider.force_flush.assert_called_once_with(
            timeout_millis=1000
        )
        self.mock_logger.debug.assert_called_with(
            f"Context does not have get_remaining_time_in_millis method or insufficient args. {USING_DEFAULT_TIMEOUT_MESSAGE}"
        )

    def test_flush_with_context_method_exception(self):
        """Test flush when context.get_remaining_time_in_millis raises exception"""
        from lumigo_opentelemetry import _flush_with_timeout

        context = MockLambdaContextWithException()
        args = ["event", context]

        _flush_with_timeout(args)

        # Should fallback to 1-second timeout
        self.mock_tracer_provider.force_flush.assert_called_once_with(
            timeout_millis=1000
        )
        self.mock_logger.warning.assert_called_with(
            f"Failed to calculate flush timeout: Failed to get remaining time. {USING_DEFAULT_TIMEOUT_MESSAGE}"
        )

    def test_flush_when_force_flush_raises_exception(self):
        """Test that force_flush exceptions are caught and logged"""
        from lumigo_opentelemetry import _flush_with_timeout

        # Make force_flush raise an exception
        self.mock_tracer_provider.force_flush.side_effect = ConnectionError(
            "Network error"
        )

        context = MockLambdaContext(remaining_time_ms=3000)
        args = ["event", context]

        with self.assertRaises(ConnectionError) as cm:
            _flush_with_timeout(args)
        self.assertEqual(str(cm.exception), "Network error")

        @pytest.mark.parametrize(
            "remaining_time_ms,expected_timeout_ms,expected_debug_timeout",
            [
                (10000, 9000, 9.0),  # (10000 - 1000) / 1000 = 9.0s
                (5000, 4500, 4.5),  # (5000 - 500) / 1000 = 4.5s
                (2000, 1800, 1.8),  # (2000 - 200) / 1000 = 1.8s
                (1500, 1350, 1.35),  # (1500 - 150) / 1000 = 1.35s
                (1200, 1080, 1.08),  # (1200 - 120) / 1000 = 1.08s
                (1000, 900, 0.9),  # (1000 - 100) / 1000 = 0.9s
                (800, 720, 0.72),  # (800 - 80) / 1000 = 0.72s
                (500, 450, 0.45),  # (500 - 50) / 1000 = 0.45s
                (200, 180, 0.18),  # (200 - 20) / 1000 = 0.18s
                (100, 90, 0.09),  # (100 - 10) / 1000 = 0.09s
            ],
        )
        def test_timeout_calculations(
            self, remaining_time_ms, expected_timeout_ms, expected_debug_timeout
        ):
            """Test timeout calculations for various remaining time scenarios"""
            from lumigo_opentelemetry import _flush_with_timeout

            context = MockLambdaContext(remaining_time_ms=remaining_time_ms)
            args = ["event", context]

            _flush_with_timeout(args)

            self.mock_tracer_provider.force_flush.assert_called_once_with(
                timeout_millis=expected_timeout_ms
            )
            self.mock_logger.debug.assert_called_with(
                f"Lambda remaining time: {remaining_time_ms}ms, calculated flush timeout: {expected_debug_timeout}s"
            )


class TestForceFlushWithTimeoutEnvironmentVariable(unittest.TestCase):
    """Test environment variable override functionality"""

    def setUp(self):
        self.tracer_provider_patcher = patch("opentelemetry.trace.get_tracer_provider")
        self.mock_tracer_provider = Mock()
        self.mock_tracer_provider_getter = self.tracer_provider_patcher.start()
        self.mock_tracer_provider_getter.return_value = self.mock_tracer_provider

        self.logger_patcher = patch("lumigo_opentelemetry.logger")
        self.mock_logger = self.logger_patcher.start()

        # Clean up environment variable for each test
        self.original_env_value = os.environ.get("LUMIGO_FLUSH_TIMEOUT")
        if "LUMIGO_FLUSH_TIMEOUT" in os.environ:
            del os.environ["LUMIGO_FLUSH_TIMEOUT"]

    def tearDown(self):
        self.tracer_provider_patcher.stop()
        self.logger_patcher.stop()

        # Restore original environment variable value
        if self.original_env_value is not None:
            os.environ["LUMIGO_FLUSH_TIMEOUT"] = self.original_env_value
        elif "LUMIGO_FLUSH_TIMEOUT" in os.environ:
            del os.environ["LUMIGO_FLUSH_TIMEOUT"]

    @patch.dict(os.environ, {"LUMIGO_FLUSH_TIMEOUT": "5000"})
    def test_custom_timeout_override_with_valid_value(self):
        """Test custom timeout override with valid environment variable"""
        from lumigo_opentelemetry import _flush_with_timeout

        context = MockLambdaContext(
            remaining_time_ms=10000
        )  # Would normally calculate 9000ms
        args = ["event", context]

        _flush_with_timeout(args)

        # Should use custom timeout instead of dynamic calculation
        self.mock_tracer_provider.force_flush.assert_called_once_with(
            timeout_millis=5000
        )
        self.mock_logger.debug.assert_called_with(
            "Using custom flush timeout from LUMIGO_FLUSH_TIMEOUT: 5000ms"
        )

    @patch.dict(os.environ, {"LUMIGO_FLUSH_TIMEOUT": "2500"})
    def test_custom_timeout_override_without_lambda_context(self):
        """Test custom timeout works even without Lambda context"""
        from lumigo_opentelemetry import _flush_with_timeout

        args = ["single_arg"]  # No Lambda context

        _flush_with_timeout(args)

        # Should use custom timeout, skip dynamic calculation entirely
        self.mock_tracer_provider.force_flush.assert_called_once_with(
            timeout_millis=2500
        )
        self.mock_logger.debug.assert_called_with(
            "Using custom flush timeout from LUMIGO_FLUSH_TIMEOUT: 2500ms"
        )

    @patch.dict(os.environ, {"LUMIGO_FLUSH_TIMEOUT": "0"})
    def test_custom_timeout_zero_value_falls_back(self):
        """Test zero timeout value falls back to default timeout"""
        from lumigo_opentelemetry import _flush_with_timeout

        context = MockLambdaContext(remaining_time_ms=5000)
        args = ["event", context]

        _flush_with_timeout(args)

        self.mock_logger.warning.assert_called_with(
            f"Invalid LUMIGO_FLUSH_TIMEOUT value '0' (must be > 0). {USING_DEFAULT_TIMEOUT_MESSAGE}"
        )
        # Should use default timeout
        self.mock_tracer_provider.force_flush.assert_called_once_with(
            timeout_millis=1000
        )

    @patch.dict(os.environ, {"LUMIGO_FLUSH_TIMEOUT": "-1000"})
    def test_custom_timeout_negative_value_falls_back(self):
        """Test negative timeout value falls back to default timeout"""
        from lumigo_opentelemetry import _flush_with_timeout

        context = MockLambdaContext(remaining_time_ms=3000)
        args = ["event", context]

        _flush_with_timeout(args)

        self.mock_logger.warning.assert_called_with(
            f"Invalid LUMIGO_FLUSH_TIMEOUT value '-1000' (must be > 0). {USING_DEFAULT_TIMEOUT_MESSAGE}"
        )
        # Should use default timeout
        self.mock_tracer_provider.force_flush.assert_called_once_with(
            timeout_millis=1000
        )

    @patch.dict(os.environ, {"LUMIGO_FLUSH_TIMEOUT": "not_a_number"})
    def test_custom_timeout_invalid_string_falls_back(self):
        """Test non-numeric timeout value falls back to default timeout"""
        from lumigo_opentelemetry import _flush_with_timeout

        context = MockLambdaContext(remaining_time_ms=4000)
        args = ["event", context]

        _flush_with_timeout(args)

        self.mock_logger.warning.assert_called_with(
            f"Failed to calculate flush timeout: invalid literal for int() with base 10: 'not_a_number'. {USING_DEFAULT_TIMEOUT_MESSAGE}"
        )
        # Should use default timeout
        self.mock_tracer_provider.force_flush.assert_called_once_with(
            timeout_millis=1000
        )

    @patch.dict(os.environ, {"LUMIGO_FLUSH_TIMEOUT": "1.5"})
    def test_custom_timeout_float_string_falls_back(self):
        """Test float string timeout value falls back to default timeout"""
        from lumigo_opentelemetry import _flush_with_timeout

        context = MockLambdaContext(remaining_time_ms=2000)
        args = ["event", context]

        _flush_with_timeout(args)

        self.mock_logger.warning.assert_called_with(
            f"Failed to calculate flush timeout: invalid literal for int() with base 10: '1.5'. {USING_DEFAULT_TIMEOUT_MESSAGE}"
        )
        # Should use default timeout
        self.mock_tracer_provider.force_flush.assert_called_once_with(
            timeout_millis=1000
        )

    def test_no_environment_variable_uses_dynamic_calculation(self):
        from lumigo_opentelemetry import _flush_with_timeout

        # Ensure environment variable is not set
        self.assertNotIn("LUMIGO_FLUSH_TIMEOUT", os.environ)

        context = MockLambdaContext(remaining_time_ms=6000)
        args = ["event", context]

        _flush_with_timeout(args)

        # Should use dynamic calculation: (6000 - 600) / 1000 = 5.4s = 5400ms
        self.mock_tracer_provider.force_flush.assert_called_once_with(
            timeout_millis=5400
        )
        self.mock_logger.debug.assert_called_with(
            "Lambda remaining time: 6000ms, calculated flush timeout: 5.4s"
        )


class TestLumigoInstrumentLambdaWithDynamicTimeout(unittest.TestCase):
    """Test lumigo_instrument_lambda decorator with dynamic timeout functionality"""

    def setUp(self):
        # Mock the flush function to avoid complex setup
        self.flush_patcher = patch("lumigo_opentelemetry._flush_with_timeout")
        self.mock_flush = self.flush_patcher.start()

        # Mock AwsLambdaInstrumentor
        self.instrumentor_patcher = patch(
            "opentelemetry.instrumentation.aws_lambda.AwsLambdaInstrumentor"
        )
        self.mock_instrumentor_class = self.instrumentor_patcher.start()
        self.mock_instrumentor = Mock()
        self.mock_instrumentor_class.return_value = self.mock_instrumentor

    def tearDown(self):
        self.flush_patcher.stop()
        self.instrumentor_patcher.stop()

    @httpretty.activate(allow_net_connect=False)
    def test_successful_lambda_execution_with_flush(self):
        """Test successful Lambda execution calls flush with correct args"""
        from lumigo_opentelemetry import lumigo_instrument_lambda

        @lumigo_instrument_lambda
        def sample_lambda(event, context):
            return {"statusCode": 200, "body": "Success"}

        context = MockLambdaContext(remaining_time_ms=5000)
        result = sample_lambda({"test": "event"}, context)

        # Verify function executed successfully
        self.assertEqual(result, {"statusCode": 200, "body": "Success"})

        # Verify instrumentation was called
        self.mock_instrumentor.instrument.assert_called_once()

        # Verify flush was called with correct args
        self.mock_flush.assert_called_once()
        args_passed_to_flush = self.mock_flush.call_args[0][0]
        self.assertEqual(args_passed_to_flush[0], {"test": "event"})
        self.assertEqual(args_passed_to_flush[1], context)

    @httpretty.activate(allow_net_connect=False)
    def test_lambda_exception_still_flushes(self):
        """Test that Lambda function exceptions don't prevent flushing"""
        from lumigo_opentelemetry import lumigo_instrument_lambda

        @lumigo_instrument_lambda
        def failing_lambda(event, context):
            raise ValueError("Something went wrong")

        context = MockLambdaContext(remaining_time_ms=3000)

        # Verify exception is raised
        with self.assertRaises(ValueError) as cm:
            failing_lambda({"test": "event"}, context)

        self.assertEqual(str(cm.exception), "Something went wrong")

        # Verify instrumentation was called
        self.mock_instrumentor.instrument.assert_called_once()

        # Verify flush was still called despite exception
        self.mock_flush.assert_called_once()
        args_passed_to_flush = self.mock_flush.call_args[0][0]
        self.assertEqual(args_passed_to_flush[0], {"test": "event"})
        self.assertEqual(args_passed_to_flush[1], context)

    @httpretty.activate(allow_net_connect=False)
    def test_lambda_with_non_lambda_context(self):
        """Test decorator works with non-Lambda context"""
        from lumigo_opentelemetry import lumigo_instrument_lambda

        @lumigo_instrument_lambda
        def regular_function(data, config):
            return data["value"] * 2

        result = regular_function({"value": 21}, {"setting": "test"})

        # Verify function executed successfully
        self.assertEqual(result, 42)

        # Verify instrumentation was called
        self.mock_instrumentor.instrument.assert_called_once()

        # Verify flush was called (will use fallback timeout)
        self.mock_flush.assert_called_once()

    @httpretty.activate(allow_net_connect=False)
    def test_lambda_with_flush_exception_doesnt_mask_original_exception(self):
        """Test that flush exceptions don't mask original Lambda exceptions"""
        from lumigo_opentelemetry import lumigo_instrument_lambda

        # Make flush raise an exception
        self.mock_flush.side_effect = RuntimeError("Flush failed")

        @lumigo_instrument_lambda
        def failing_lambda(event, context):
            raise ValueError("Original Lambda error")

        context = MockLambdaContext(remaining_time_ms=2000)

        # Verify the ORIGINAL exception is raised, not the flush exception
        with self.assertRaises(ValueError) as cm:
            failing_lambda({"test": "event"}, context)

        self.assertEqual(str(cm.exception), "Original Lambda error")

        # Verify flush was attempted
        self.mock_flush.assert_called_once()

    @httpretty.activate(allow_net_connect=False)
    def test_force_flush_timeout_with_lambda_context_no_env_var(self):
        """Test that force_flush is called with correct dynamic timeout when no env var is set"""
        # Don't mock the flush function, mock the tracer provider instead to test actual timeout
        self.flush_patcher.stop()

        tracer_provider_patcher = patch("opentelemetry.trace.get_tracer_provider")
        mock_tracer_provider = Mock()
        mock_tracer_provider_getter = tracer_provider_patcher.start()
        mock_tracer_provider_getter.return_value = mock_tracer_provider

        logger_patcher = patch("lumigo_opentelemetry.logger")

        try:
            from lumigo_opentelemetry import lumigo_instrument_lambda

            @lumigo_instrument_lambda
            def sample_lambda(event, context):
                return {"statusCode": 200, "body": "Success"}

            context = MockLambdaContext(remaining_time_ms=5000)
            result = sample_lambda({"test": "event"}, context)

            # Verify function executed successfully
            self.assertEqual(result, {"statusCode": 200, "body": "Success"})

            # Verify force_flush was called with calculated timeout: (5000 - 500) / 1000 = 4.5s = 4500ms
            mock_tracer_provider.force_flush.assert_called_once_with(
                timeout_millis=4500
            )

        finally:
            tracer_provider_patcher.stop()
            logger_patcher.stop()
            # Restart the original flush patcher for other tests
            self.flush_patcher = patch("lumigo_opentelemetry._flush_with_timeout")
            self.mock_flush = self.flush_patcher.start()

    @httpretty.activate(allow_net_connect=False)
    @patch.dict(os.environ, {"LUMIGO_FLUSH_TIMEOUT": "2500"})
    def test_force_flush_timeout_with_env_var_override(self):
        """Test that force_flush is called with env var timeout when LUMIGO_FLUSH_TIMEOUT is set"""
        # Don't mock the flush function, mock the tracer provider instead to test actual timeout
        self.flush_patcher.stop()

        tracer_provider_patcher = patch("opentelemetry.trace.get_tracer_provider")
        mock_tracer_provider = Mock()
        mock_tracer_provider_getter = tracer_provider_patcher.start()
        mock_tracer_provider_getter.return_value = mock_tracer_provider

        logger_patcher = patch("lumigo_opentelemetry.logger")

        try:
            from lumigo_opentelemetry import lumigo_instrument_lambda

            @lumigo_instrument_lambda
            def sample_lambda(event, context):
                return {"statusCode": 200, "body": "Success"}

            context = MockLambdaContext(
                remaining_time_ms=10000
            )  # Would normally calculate 9000ms
            result = sample_lambda({"test": "event"}, context)

            # Verify function executed successfully
            self.assertEqual(result, {"statusCode": 200, "body": "Success"})

            # Verify force_flush was called with env var timeout (2500ms) instead of calculated (9000ms)
            mock_tracer_provider.force_flush.assert_called_once_with(
                timeout_millis=2500
            )

        finally:
            tracer_provider_patcher.stop()
            logger_patcher.stop()
            # Restart the original flush patcher for other tests
            self.flush_patcher = patch("lumigo_opentelemetry._flush_with_timeout")
            self.mock_flush = self.flush_patcher.start()
