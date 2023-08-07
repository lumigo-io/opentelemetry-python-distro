from typing import Union

from opentelemetry.trace.span import Span

from lumigo_opentelemetry.libs.general_utils import lumigo_safe_execute

PAYLOAD_MAX_SIZE = 2048


def add_body_attribute(
    span: Span, body: Union[str, bytes, None], attr_name: str
) -> None:
    with lumigo_safe_execute(f"set body attribute ({attr_name})"):
        if isinstance(body, str):
            value = body[:PAYLOAD_MAX_SIZE]
        elif isinstance(body, bytes):
            try:
                value = body.decode("utf-8")[:PAYLOAD_MAX_SIZE]
            except UnicodeDecodeError:
                value = "0x" + body.hex()[:PAYLOAD_MAX_SIZE]
        else:
            value = str(body)

        span.set_attribute(attr_name, value)
