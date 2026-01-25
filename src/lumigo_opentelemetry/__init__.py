from __future__ import annotations

import logging
import os
import sys
from functools import wraps
from typing import Any, Callable, Dict, List, TypeVar


from lumigo_opentelemetry.utils.span_processor_utils import add_execution_tags
from lumigo_opentelemetry.utils.span_processor_utils import detach_execution_tags


LOG_FORMAT = "#LUMIGO# - %(asctime)s - %(levelname)s - %(message)s"
DEFAULT_TIMEOUT_MS = 1000
MAX_FLUSH_TIMEOUT_MS = 10000  # 10 seconds
USING_DEFAULT_TIMEOUT_MESSAGE = f"Using default {DEFAULT_TIMEOUT_MS}ms timeout."

T = TypeVar("T")


def _setup_logger(logger_name: str = "lumigo-opentelemetry") -> logging.Logger:
    """
    This function returns Lumigo's logger. The Lumigo logger prints to stderr.
    The Lumigo logger is set to INFO by default. If the environment variable
    `LUMIGO_DEBUG=true` is set, the severity is set to DEBUG.
    """
    _logger = logging.getLogger(logger_name)
    _logger.propagate = False
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(LOG_FORMAT))
    if os.environ.get("LUMIGO_DEBUG", "").lower() == "true":
        _logger.setLevel(logging.DEBUG)
    else:
        _logger.setLevel(logging.INFO)
    _logger.addHandler(handler)

    # Suppress spurious warnings when the application is not running on ECS
    logging.getLogger("opentelemetry.sdk.extension.aws.resource.ecs").setLevel(
        logging.CRITICAL
    )

    # Suppress spurious warnings when the application is not running on EKS
    logging.getLogger("opentelemetry.sdk.extension.aws.resource.eks").setLevel(
        logging.CRITICAL
    )

    return _logger


logger = _setup_logger()


def _get_lumigo_opentelemetry_version() -> str:
    try:
        with open(os.path.join(os.path.dirname(__file__), "VERSION")) as version_file:
            return version_file.read().strip()
    except Exception as err:
        logger.exception("failed getting lumigo_opentelemetry version", exc_info=err)
        return "unknown"


def _get_lumigo_sampler() -> Any:
    # import here to avoid circular imports
    from lumigo_opentelemetry.libs.sampling import LUMIGO_SAMPLER

    return LUMIGO_SAMPLER


__version__ = _get_lumigo_opentelemetry_version()


def auto_load(_: Any) -> None:
    """
    Called when injection performed over `AUTOWRAPT_BOOTSTRAP`.
    """
    # Some versions of Python have issues with the 'argv' attribute when
    # auto-loading the tracer. See https://bugs.python.org/issue32573
    import sys

    if not hasattr(sys, "argv"):
        sys.argv = [""]

    # We do not need to init the package, it will happen automatically due
    # to the init() call at the end of this file.


def init() -> Dict[str, Any]:
    """Initialize the Lumigo OpenTelemetry distribution."""

    try:
        python_version = sys.version_info
        # Check if the major version is 3 and the minor version is between 9 and 14
        if python_version.major != 3 or not (9 <= python_version.minor <= 14):
            logger.warning(
                f"Unsupported Python version {python_version.major}.{python_version.minor}; "
                "only Python 3.9 to 3.14 are supported."
            )
            return {}

    except Exception as e:  # Catch any issues with accessing sys.version_info
        # Log a warning if there is a failure in verifying the Python version
        logger.warning("Failed to verify the Python version due to: %s", str(e))
        return {}

    if str(os.environ.get("LUMIGO_SWITCH_OFF", False)).lower() == "true":
        logger.info(
            "Lumigo OpenTelemetry distribution disabled via the 'LUMIGO_SWITCH_OFF' environment variable"
        )
        return {}

    # Multiple packages are passed to autowrapt in comma-separated form
    if "lumigo_opentelemetry" in os.getenv("AUTOWRAPT_BOOTSTRAP", "").split(","):
        activation_mode = "automatic injection"
    else:
        activation_mode = "import"

    logger.info(
        f"Loading the Lumigo OpenTelemetry distribution v{__version__} (injection mode: %s)",
        activation_mode,
    )

    from opentelemetry import trace
    from opentelemetry import _logs
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk.trace import SpanLimits, TracerProvider
    from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
    from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
    from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
    from opentelemetry.instrumentation.logging import LoggingInstrumentor
    from lumigo_opentelemetry.resources.span_processor import (
        LumigoSpanProcessor,
        LumigoExecutionTagProcessor,
    )

    LUMIGO_ENDPOINT_BASE_URL = "https://ga-otlp.lumigo-tracer-edge.golumigo.com/v1"

    DEFAULT_LUMIGO_ENDPOINT = f"{LUMIGO_ENDPOINT_BASE_URL}/traces"
    DEFAULT_LUMIGO_LOGS_ENDPOINT = f"{LUMIGO_ENDPOINT_BASE_URL}/logs"
    DEFAULT_DEPENDENCIES_ENDPOINT = f"{LUMIGO_ENDPOINT_BASE_URL}/dependencies"

    lumigo_traces_endpoint = os.getenv("LUMIGO_ENDPOINT", DEFAULT_LUMIGO_ENDPOINT)
    lumigo_logs_endpoint = os.getenv(
        "LUMIGO_LOGS_ENDPOINT", DEFAULT_LUMIGO_LOGS_ENDPOINT
    )
    lumigo_token = os.getenv("LUMIGO_TRACER_TOKEN")
    lumigo_report_dependencies = (
        os.getenv("LUMIGO_REPORT_DEPENDENCIES", "true").lower() == "true"
    )
    logging_enabled = os.getenv("LUMIGO_ENABLE_LOGS", "false").lower() == "true"
    tracing_enabled = os.getenv("LUMIGO_ENABLE_TRACES", "true").lower() == "true"
    spandump_file = os.getenv("LUMIGO_DEBUG_SPANDUMP")
    logdump_file = os.getenv("LUMIGO_DEBUG_LOGDUMP")

    # Activate instrumentations
    from lumigo_opentelemetry.instrumentations import instrumentations  # noqa
    from lumigo_opentelemetry.instrumentations.instrumentations import framework
    from lumigo_opentelemetry.libs.general_utils import get_max_size
    from lumigo_opentelemetry.processors.logs_processor import LumigoLogRecordProcessor
    from lumigo_opentelemetry.resources.detectors import (
        get_infrastructure_resource,
        get_process_resource,
        get_resource,
    )
    import re
    from opentelemetry.sdk.trace import IdGenerator, RandomIdGenerator

    class LambdaTraceIdGenerator(IdGenerator):
        random_id_generator = RandomIdGenerator()

        def generate_span_id(self) -> int:
            return self.random_id_generator.generate_span_id()  # type: ignore

        def generate_trace_id(self) -> int:
            match = re.search(
                r"Root=1-[\da-f]+-([\da-f]{24})",
                os.environ.get("_X_AMZN_TRACE_ID", ""),
                re.IGNORECASE,
            )
            if match:
                trace_id = match.group(1)
                if len(trace_id) == 24:
                    return int(trace_id, 16) << 32
            return self.random_id_generator.generate_trace_id()  # type: ignore

    infrastructure_resource = get_infrastructure_resource()
    process_resource = get_process_resource()

    resource = get_resource(
        infrastructure_resource, process_resource, {"framework": framework}
    )

    tracer_provider = TracerProvider(
        resource=resource,
        sampler=_get_lumigo_sampler(),
        span_limits=(SpanLimits(max_span_attribute_length=(get_max_size()))),
        id_generator=LambdaTraceIdGenerator(),
    )

    tracer_provider.add_span_processor(LumigoExecutionTagProcessor())

    logger_provider = LoggerProvider(resource=resource)
    logger_provider.add_log_record_processor(LumigoLogRecordProcessor())

    if lumigo_token:
        if tracing_enabled:
            tracer_provider.add_span_processor(
                LumigoSpanProcessor(
                    OTLPSpanExporter(
                        endpoint=lumigo_traces_endpoint,
                        headers={"Authorization": f"LumigoToken {lumigo_token}"},
                    ),
                )
            )
        else:
            logger.info(
                'Tracing is disabled (the "LUMIGO_ENABLE_TRACES" environment variable is not set to "true"): no traces will be sent to Lumigo.'
            )

        if logging_enabled:
            logger_provider.add_log_record_processor(
                BatchLogRecordProcessor(
                    OTLPLogExporter(
                        endpoint=lumigo_logs_endpoint,
                        headers={"Authorization": f"LumigoToken {lumigo_token}"},
                    )
                )
            )
        else:
            logger.info(
                'Logging is disabled (the "LUMIGO_ENABLE_LOGS" environment variable is not set to "true"): no logs will be sent to Lumigo.'
            )

        if lumigo_report_dependencies:
            from lumigo_opentelemetry.dependencies import report

            try:
                report(
                    DEFAULT_DEPENDENCIES_ENDPOINT,
                    lumigo_token,
                    infrastructure_resource.attributes,
                )
            except Exception as e:
                logger.debug("Cannot report dependencies to Lumigo", exc_info=e)
        else:
            logger.debug("Dependency reporting is turned off")
    else:
        logger.warning(
            "Lumigo token not provided (env var 'LUMIGO_TRACER_TOKEN' not set); "
            "no data will be sent to Lumigo"
        )

    if spandump_file:
        from opentelemetry.sdk.trace.export import (
            ConsoleSpanExporter,
            SimpleSpanProcessor,
        )

        tracer_provider.add_span_processor(
            SimpleSpanProcessor(
                ConsoleSpanExporter(
                    out=open(spandump_file, "w"),
                    # Print one span per line for ease of parsing, as the
                    # file itself will not be valid JSON, it will be just a
                    # sequence of JSON objects, not a list
                    formatter=lambda span: span.to_json(indent=None) + "\n",
                )
            )
        )

        logger.debug("Storing a copy of the trace data under: %s", spandump_file)

    trace.set_tracer_provider(tracer_provider)

    if logging_enabled:
        _logs.set_logger_provider(logger_provider)

        # Add the handler to the root logger, hence affecting all loggers created by the app from now on
        logging.getLogger().addHandler(LoggingHandler(logger_provider=logger_provider))

        # Inject the span context into logs
        LoggingInstrumentor().instrument(set_logging_format=True)

        if logdump_file:
            from opentelemetry.sdk._logs.export import (
                ConsoleLogExporter,
                SimpleLogRecordProcessor,
            )

            try:
                output = open(logdump_file, "w")
            except Exception:
                logger.error(
                    f"Cannot open the log dump file for writing: {logdump_file}"
                )
                output = sys.stdout  # type: ignore

            logger_provider.add_log_record_processor(
                SimpleLogRecordProcessor(
                    ConsoleLogExporter(
                        out=output,
                        # Override the default formatter to remove indentation, so one log record will be printed per line
                        formatter=lambda log_record: log_record.to_json(indent=None)
                        + "\n",
                    )
                )
            )

            logger.debug("Storing a copy of the log data under: %s", logdump_file)

    return {"tracer_provider": tracer_provider, "logger_provider": logger_provider}


def _calculate_flush_timeout(args: List[Any]) -> int:
    """
    Calculate flush timeout based on Lambda context remaining time.
    Supports environment variable override via LUMIGO_FLUSH_TIMEOUT.

    Args:
        args: Function arguments where args[1] should be Lambda context if available

    Returns:
        Timeout in milliseconds
    """
    timeout_ms = DEFAULT_TIMEOUT_MS
    try:
        custom_timeout_env = os.getenv("LUMIGO_FLUSH_TIMEOUT")
        if custom_timeout_env:
            custom_timeout_ms = int(custom_timeout_env)
            if custom_timeout_ms > 0:
                timeout_ms = custom_timeout_ms
                logger.debug(
                    f"Using custom flush timeout from LUMIGO_FLUSH_TIMEOUT: {timeout_ms}ms"
                )
            else:
                logger.warning(
                    f"Invalid LUMIGO_FLUSH_TIMEOUT value '{custom_timeout_env}' (must be > 0). {USING_DEFAULT_TIMEOUT_MESSAGE}"
                )
        else:
            if len(args) >= 2 and hasattr(args[1], "get_remaining_time_in_millis"):
                context = args[1]
                remaining_time_ms = context.get_remaining_time_in_millis()
                timeout_ms = int(remaining_time_ms * 0.90)
                if timeout_ms > MAX_FLUSH_TIMEOUT_MS:
                    timeout_ms = MAX_FLUSH_TIMEOUT_MS

                logger.debug(
                    f"Lambda remaining time: {remaining_time_ms}ms, calculated flush timeout: {timeout_ms}ms"
                )
            else:
                logger.debug(
                    f"Context does not have get_remaining_time_in_millis method or insufficient args. {USING_DEFAULT_TIMEOUT_MESSAGE}"
                )
    except Exception as e:
        logger.warning(
            f"Failed to calculate flush timeout: {e}. {USING_DEFAULT_TIMEOUT_MESSAGE}"
        )

    return timeout_ms


def lumigo_instrument_lambda(func: Callable[..., T]) -> Callable[..., T]:
    from opentelemetry.instrumentation.aws_lambda import AwsLambdaInstrumentor
    from opentelemetry import trace
    from lumigo_opentelemetry.libs.json_utils import dump

    # Validate function has required attributes
    if not hasattr(func, "__module__") or func.__module__ is None:
        logger.warning("Function missing __module__ attribute, returning unwrapped")
        return func

    if not hasattr(func, "__name__"):
        logger.warning("Function missing __name__ attribute, returning unwrapped")
        return func

    try:
        mod = sys.modules[func.__module__]
    except KeyError:
        logger.warning(
            f"Module {func.__module__} not found in sys.modules, returning unwrapped"
        )
        return func

    name = func.__name__

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Dict[Any, Any]) -> T:
        # Capture event and context from Lambda arguments
        event = args[0] if len(args) > 0 else None
        context = args[1] if len(args) > 1 else None

        # Set AwsLambdaInstrumentor flush timeout based on remaining time
        # Only set if not already configured by user
        if "OTEL_INSTRUMENTATION_AWS_LAMBDA_FLUSH_TIMEOUT" not in os.environ:
            timeout_ms = _calculate_flush_timeout(list(args))
            os.environ["OTEL_INSTRUMENTATION_AWS_LAMBDA_FLUSH_TIMEOUT"] = str(
                timeout_ms
            )

        # Get current span to add attributes
        current_span = trace.get_current_span()

        # Set event attributes on the current span
        if current_span and current_span.is_recording():
            current_span.set_attribute(
                "faas.event", dump(event) if event is not None else "null"
            )

            if context is not None:
                if hasattr(context, "function_name"):
                    current_span.set_attribute("faas.name", context.function_name)
                if hasattr(context, "aws_request_id"):
                    current_span.set_attribute("faas.execution", context.aws_request_id)

        try:
            result = func(*args, **kwargs)

            # Set return value attribute on the current span
            if current_span and current_span.is_recording():
                current_span.set_attribute(
                    "faas.return_value", dump(result) if result is not None else "null"
                )

            return result
        except Exception as e:
            # Record exception on the current span
            if current_span and current_span.is_recording():
                current_span.record_exception(e)
            raise
        finally:
            # Ensure we detach any contexts to avoid leakage across warm invocations
            try:
                detach_execution_tags()
            except Exception:
                logger.debug(
                    "Failed to detach execution tags in Lambda wrapper", exc_info=True
                )

    # Safely replace function in module namespace
    try:
        setattr(mod, name, wrapper)
        AwsLambdaInstrumentor().instrument(
            tracer_provider=trace.get_tracer_provider(),
        )
        return getattr(mod, name)  # type: ignore
    except (AttributeError, TypeError) as e:
        logger.error(
            f"Failed to replace function in module: {e}, returning wrapper directly"
        )
        AwsLambdaInstrumentor().instrument(
            tracer_provider=trace.get_tracer_provider(),
        )
        return wrapper


def lumigo_wrapped(func: Callable[..., T]) -> Callable[..., T]:
    CONTEXT_NAME = "lumigo"
    PARENT_IDENTICATOR = "LumigoRoot"

    from opentelemetry import trace

    from lumigo_opentelemetry.libs.json_utils import dump

    def wrapper(*args: List[Any], **kwargs: Dict[Any, Any]) -> T:
        tracer = trace.get_tracer_provider().get_tracer(CONTEXT_NAME)
        with tracer.start_as_current_span(PARENT_IDENTICATOR) as span:
            span.set_attribute("input_args", dump(args))
            span.set_attribute("input_kwargs", dump(kwargs))
            return_value = func(*args, **kwargs)
            span.set_attribute("return_value", dump(return_value))
            return return_value

    return wrapper


def create_programmatic_error(error_message: str, error_type: str) -> None:
    from opentelemetry.trace import get_current_span

    get_current_span().add_event(error_message, {"lumigo.type": error_type})


# Load the package on import
init_data = init()

tracer_provider = init_data.get("tracer_provider")
logger_provider = init_data.get("logger_provider")

__all__ = [
    "auto_load",
    "init",
    "lumigo_wrapped",
    "logger",
    "tracer_provider",
    "logger_provider",
    "create_programmatic_error",
    "add_execution_tags",
]
