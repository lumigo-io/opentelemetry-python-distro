from __future__ import annotations

import logging
import os

LOG_FORMAT = "#LUMIGO# - %(asctime)s - %(levelname)s - %(message)s"


def _setup_logger(logger_name="lumigo-opentelemetry"):
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
    return _logger


logger = _setup_logger()


def auto_load(_):
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


def init():
    if str(os.environ.get("LUMIGO_SWITCH_OFF", False)).lower() == "true":
        logger.info(
            "Lumigo OpenTelemetry distribution disabled via the 'LUMIGO_SWITCH_OFF' environment variable"
        )
        return

    # Multiple packages are passed to autowrapt in comma-separated form
    if "lumigo_opentelemetry" in os.getenv("AUTOWRAPT_BOOTSTRAP", "").split(","):
        activation_mode = "automatic injection"
    else:
        activation_mode = "import"

    logger.info(
        "Loading the Lumigo OpenTelemetry distribution (injection mode: %s)",
        activation_mode,
    )

    from opentelemetry import trace
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk.resources import OTELResourceDetector, Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    from lumigo_opentelemetry.libs.json_utils import dump
    from lumigo_opentelemetry.resources.detectors import (
        AwsEcsResourceDetector,
        LumigoDistroDetector,
        ProcessResourceDetector,
    )

    DEFAULT_LUMIGO_ENDPOINT = (
        "https://ga-otlp.lumigo-tracer-edge.golumigo.com/v1/traces"
    )

    lumigo_endpoint = os.getenv("LUMIGO_ENDPOINT", DEFAULT_LUMIGO_ENDPOINT)

    def safe_get_envs() -> str:
        try:
            return dump(dict(os.environ))
        except Exception as e:
            logger.exception("failed getting envs", exc_info=e)
            return ""

    lumigo_token = os.getenv("LUMIGO_TRACER_TOKEN")

    # Activate instrumentations
    from lumigo_opentelemetry.instrumentations import instrumentations  # noqa
    from lumigo_opentelemetry.instrumentations.instrumentations import framework

    # TODO Clean up needed
    attributes = {
        # TODO Use a Resource Detector instead
        "envs": safe_get_envs(),
        "framework": framework,
    }

    if lumigo_token:
        # TODO Remove from resource attributes as soon as the edge endpoint supports token in HTTP headers
        attributes["lumigoToken"] = lumigo_token.strip()

    tracer_resource = (Resource.create(attributes=attributes)
        .merge(OTELResourceDetector().detect())
        .merge(ProcessResourceDetector().detect())
        .merge(LumigoDistroDetector().detect())
        .merge(AwsEcsResourceDetector().detect())
    )
    tracer_provider = TracerProvider(resource=tracer_resource)

    if lumigo_token:
        tracer_provider.add_span_processor(
            BatchSpanProcessor(
                OTLPSpanExporter(
                    endpoint=lumigo_endpoint,
                    headers={"Authorization": f"LumigoToken {lumigo_token}"},
                ),
            )
        )
    else:
        logger.warning(
            "Lumigo token not provided (env var 'LUMIGO_TRACER_TOKEN' not set); "
            "no data will be sent to Lumigo"
        )

    spandump_file = os.getenv("LUMIGO_DEBUG_SPANDUMP")
    if spandump_file:
        from opentelemetry.sdk.trace.export import (
            SimpleSpanProcessor,
            ConsoleSpanExporter,
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


def lumigo_wrapped(func):
    CONTEXT_NAME = "lumigo"
    PARENT_IDENTICATOR = "LumigoRoot"

    from opentelemetry import trace
    from lumigo_opentelemetry.libs.json_utils import dump

    def wrapper(*args, **kwargs):
        tracer = trace.get_tracer_provider().get_tracer(CONTEXT_NAME)
        with tracer.start_as_current_span(PARENT_IDENTICATOR) as span:
            span.set_attribute("input_args", dump(args))
            span.set_attribute("input_kwargs", dump(kwargs))
            return_value = func(*args, **kwargs)
            span.set_attribute("return_value", dump(return_value))
            return return_value

    return wrapper

with open(os.path.join(os.path.dirname(__file__), 'Version')) as version_file:
    __version__ = version_file.read().strip()

__all__ = ["auto_load", "init", "lumigo_wrapped", "logger"]

# Load the package on import
init()
