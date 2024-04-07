from lumigo_opentelemetry import logger_provider
import logging

logger = logging.getLogger(__name__)

logger.setLevel(logging.DEBUG)

logger.debug("Hello OTEL!")

logger_provider.force_flush()
logger_provider.shutdown()
