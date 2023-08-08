import os
from typing import Callable, Any

from opentelemetry.trace import get_current_span
from lumigo_opentelemetry.libs.general_utils import lumigo_safe_execute
from lumigo_opentelemetry import logger
from lumigo_opentelemetry.instrumentations.instrumentation_utils import PAYLOAD_MAX_SIZE

SHOULD_INSTRUMENT_PAYLOADS = (
    os.getenv("LUMIGO_INSTRUMENT_GRPC_PAYLOADS", "true").lower() != "false"
)


def add_payload_in_bulks(attribute_name: str) -> Callable[[str], None]:
    history = []
    remaining_size = PAYLOAD_MAX_SIZE

    def add_payload(payload: Any) -> None:
        """Add the payload to the current span.

        :param payload: The payload to add.
        """
        with lumigo_safe_execute("add_payload_in_bulks"):
            nonlocal remaining_size
            if remaining_size > 0:
                history.append(str(payload))
                get_current_span().set_attribute(
                    attribute_name, ",".join(history)[:PAYLOAD_MAX_SIZE]
                )
                remaining_size -= len(history[-1])
                if remaining_size <= 0:
                    logger.debug(
                        f"gRPC: payload size limit reached ({PAYLOAD_MAX_SIZE})"
                    )

    return add_payload
