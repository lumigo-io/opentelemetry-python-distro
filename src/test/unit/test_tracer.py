import os
import sys
import unittest
import httpretty

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

    def test_function_without_module_attribute(self):
        """Test decorator handles functions without __module__ gracefully"""
        from lumigo_opentelemetry import lumigo_instrument_lambda

        # Create a function-like object without __module__
        class FakeFunc:
            def __call__(self, x, y):
                return x + y

        fake_func = FakeFunc()
        result = lumigo_instrument_lambda(fake_func)
        self.assertIs(result, fake_func)  # Should return original function

    def test_function_without_name_attribute(self):
        """Test decorator handles functions without __name__ gracefully"""
        from lumigo_opentelemetry import lumigo_instrument_lambda

        # Create a function-like object without __name__
        class FuncWithoutName:
            def __call__(self):
                return "test"

        sample_func = FuncWithoutName()

        result = lumigo_instrument_lambda(sample_func)
        self.assertIs(result, sample_func)  # Should return original function

    def test_function_with_none_module(self):
        """Test decorator handles functions with None __module__"""
        from lumigo_opentelemetry import lumigo_instrument_lambda

        def sample_func():
            return "test"

        sample_func.__module__ = None

        result = lumigo_instrument_lambda(sample_func)
        self.assertIs(result, sample_func)  # Should return original function

    def test_function_module_not_in_sys_modules(self):
        """Test decorator handles missing module in sys.modules"""
        from lumigo_opentelemetry import lumigo_instrument_lambda

        def sample_func():
            return "test"

        sample_func.__module__ = "nonexistent_module"

        result = lumigo_instrument_lambda(sample_func)
        self.assertIs(result, sample_func)  # Should return original function

    def test_setattr_failure_on_readonly_module(self):
        """Test decorator handles setattr failure gracefully"""
        from lumigo_opentelemetry import lumigo_instrument_lambda

        # Create a module-like object that raises on setattr
        class ReadOnlyModule:
            def __setattr__(self, name, value):
                raise AttributeError("Read-only module")

        readonly_module = ReadOnlyModule()

        def sample_func():
            return "test"

        sample_func.__module__ = "test_module"

        # Mock sys.modules to return our readonly module
        import sys

        original_module = sys.modules.get("test_module")
        sys.modules["test_module"] = readonly_module

        try:
            # Should not raise exception, should return wrapper directly
            result = lumigo_instrument_lambda(sample_func)
            self.assertIsNotNone(result)
            self.assertNotEqual(result, sample_func)  # Should be wrapper
        finally:
            # Cleanup
            if original_module is None:
                sys.modules.pop("test_module", None)
            else:
                sys.modules["test_module"] = original_module

    def test_module_namespace_replacement(self):
        """Test that function is properly replaced in module namespace"""
        import sys
        from lumigo_opentelemetry import lumigo_instrument_lambda

        # Create a test module
        test_module = type(sys)("test_replacement_module")
        sys.modules["test_replacement_module"] = test_module

        def sample_func():
            return "original"

        sample_func.__module__ = "test_replacement_module"
        sample_func.__name__ = "sample_func"

        # Set original function in module
        setattr(test_module, "sample_func", sample_func)

        # Decorate
        result = lumigo_instrument_lambda(sample_func)

        # Check that module now contains the wrapper
        module_func = getattr(test_module, "sample_func")
        self.assertIs(result, module_func)
        self.assertNotEqual(module_func, sample_func)  # Should be wrapper

        # Cleanup
        del sys.modules["test_replacement_module"]

    def test_event_and_return_value_capture(self):
        """Test that event and return_value are captured in span attributes"""
        from lumigo_opentelemetry import lumigo_instrument_lambda
        from unittest.mock import Mock, patch
        import json

        # Mock the current span to verify attributes are set
        mock_span = Mock()
        mock_span.is_recording.return_value = True

        with patch("opentelemetry.trace.get_current_span", return_value=mock_span):

            @lumigo_instrument_lambda
            def lambda_handler(event, context):
                return {
                    "statusCode": 200,
                    "body": f"Hello, {event.get('name', 'World')}!",
                }

            # Test event and return value capture
            test_event = {"name": "Claude", "requestId": "12345"}
            test_context = {"requestId": "12345", "functionName": "test-function"}

            result = lambda_handler(test_event, test_context)

            # Verify return value
            self.assertEqual(result["statusCode"], 200)
            self.assertIn("Hello, Claude!", result["body"])

            # Verify that set_attribute was called with our expected attributes
            set_attribute_calls = mock_span.set_attribute.call_args_list

            # Check for faas.event attribute
            event_attr_call = None
            return_attr_call = None

            for call in set_attribute_calls:
                args, kwargs = call
                if args[0] == "faas.event":
                    event_attr_call = call
                elif args[0] == "faas.return_value":
                    return_attr_call = call

            # Verify event attribute was set
            self.assertIsNotNone(
                event_attr_call, "faas.event attribute should have been set"
            )
            event_data = json.loads(event_attr_call[0][1])
            self.assertEqual(event_data["name"], "Claude")
            self.assertEqual(event_data["requestId"], "12345")

            # Verify return value attribute was set
            self.assertIsNotNone(
                return_attr_call, "faas.return_value attribute should have been set"
            )
            return_data = json.loads(return_attr_call[0][1])
            self.assertEqual(return_data["statusCode"], 200)
            self.assertIn("Hello, Claude!", return_data["body"])


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

    def test_flush_with_lambda_context_take_max_timeout(self):
        from lumigo_opentelemetry import _flush_with_timeout

        context = MockLambdaContext(remaining_time_ms=80000)
        args = ["event", context]

        _flush_with_timeout(args)

        # Should take max timeout
        self.mock_tracer_provider.force_flush.assert_called_once_with(
            timeout_millis=10000
        )
        self.mock_logger.debug.assert_called_with(
            "Lambda remaining time: 80000ms, calculated flush timeout: 10000ms"
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

    @httpretty.activate(allow_net_connect=False)
    @patch.dict(os.environ, {"LUMIGO_FLUSH_TIMEOUT": "1.5"})
    def test_force_flush_timeout_with_unsupported_env_var_value_falls_back(self):
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
                timeout_millis=1000
            )

        finally:
            tracer_provider_patcher.stop()
            logger_patcher.stop()
            # Restart the original flush patcher for other tests
            self.flush_patcher = patch("lumigo_opentelemetry._flush_with_timeout")
            self.mock_flush = self.flush_patcher.start()
