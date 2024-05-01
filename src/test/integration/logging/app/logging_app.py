from lumigo_opentelemetry import logger_provider, tracer_provider
import logging

tracer = tracer_provider.get_tracer(__file__)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def write_log(message):
    log = {
        "some-thing": message,
        "some-super-sekret-stuff": "this is a secret",
    }

    logger.debug(log)


write_log(message="with no recording span")

with tracer.start_as_current_span("some-span") as span:
    write_log("with recording span")

logger_provider.force_flush()
logger_provider.shutdown()
