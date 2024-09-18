from __future__ import annotations

import logging
import os
import sys
from typing import Any, Callable, Dict, List, TypeVar

LOG_FORMAT = "#LUMIGO# - %(asctime)s - %(levelname)s - %(message)s"

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
        # Check if the major version is 3 and the minor version is between 8 and 12
        if python_version.major != 3 or not (8 <= python_version.minor <= 12):
            logger.warning(
                f"Unsupported Python version {python_version.major}.{python_version.minor}; "
                "only Python 3.8 to 3.12 are supported."
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
    from lumigo_opentelemetry.resources.span_processor import LumigoSpanProcessor

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
    logging_enabled = os.getenv("LUMIGO_ENABLE_LOGS", "").lower() == "true"
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

    infrastructure_resource = get_infrastructure_resource()
    process_resource = get_process_resource()

    resource = get_resource(
        infrastructure_resource, process_resource, {"framework": framework}
    )

    tracer_provider = TracerProvider(
        resource=resource,
        sampler=_get_lumigo_sampler(),
        span_limits=(SpanLimits(max_span_attribute_length=(get_max_size()))),
    )

    logger_provider = LoggerProvider(resource=resource)
    logger_provider.add_log_record_processor(LumigoLogRecordProcessor())

    if lumigo_token:
        tracer_provider.add_span_processor(
            LumigoSpanProcessor(
                OTLPSpanExporter(
                    endpoint=lumigo_traces_endpoint,
                    headers={"Authorization": f"LumigoToken {lumigo_token}"},
                ),
            )
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
]
