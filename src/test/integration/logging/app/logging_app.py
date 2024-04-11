import json
import os
from opentelemetry import trace
from lumigo_opentelemetry import logger_provider
import logging

tracer = trace.get_tracer(__file__)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

with tracer.start_as_current_span("some-span") as span:
    message = {
        "some-thing": "Hello OTEL!",
        "some-super-secret-stuff": "this is a secret",
    }

    if os.environ["LOG_AS_JSON_STRING"] == "true":
        logger.debug(json.dumps(message))
    else:
        logger.debug(message)

    logger_provider.force_flush()
    logger_provider.shutdown()
