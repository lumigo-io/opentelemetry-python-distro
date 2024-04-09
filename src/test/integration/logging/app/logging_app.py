from opentelemetry import trace
from lumigo_opentelemetry import logger_provider
import logging

tracer = trace.get_tracer(__file__)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

with tracer.start_as_current_span("some-span") as span:
    logger.debug("Hello OTEL!")

    logger_provider.force_flush()
    logger_provider.shutdown()
