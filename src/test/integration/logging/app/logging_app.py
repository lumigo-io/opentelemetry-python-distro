from opentelemetry import trace
from opentelemetry.trace.span import format_span_id, format_trace_id
from lumigo_opentelemetry import logger_provider
import logging

tracer = trace.get_tracer(__file__)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

with tracer.start_as_current_span("some-span") as span:
    logger.debug(
        "Hello OTEL!",
        extra={
            "span_id": format_span_id(span.get_span_context().span_id),
            "trace_id": format_trace_id(span.get_span_context().trace_id),
        },
    )

    logger_provider.force_flush()
    logger_provider.shutdown()
