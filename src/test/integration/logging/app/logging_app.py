import json
import os
from lumigo_opentelemetry import logger_provider, tracer_provider
import logging

tracer = tracer_provider.get_tracer(__file__)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def write_log(message):
    log = {
        "some-thing": message,
        "some-super-secret-stuff": "this is a secret",
    }

    if os.environ["LOG_AS_STRING"] == "true":
        logger.debug(json.dumps(log))
    else:
        logger.debug(log)


write_log("with no recording span")

with tracer.start_as_current_span("some-span") as span:
    write_log("with recording span")

logger_provider.force_flush()
logger_provider.shutdown()
