from opentelemetry.trace.span import Span
from lumigo_opentelemetry.instrumentations import AbstractInstrumentor
from lumigo_opentelemetry.instrumentations.instrumentation_utils import (
    add_body_attribute,
)


class PikaInstrumentor(AbstractInstrumentor):
    def __init__(self) -> None:
        super().__init__("pika")

    def check_if_applicable(self) -> None:
        import pika  # noqa

    def install_instrumentation(self) -> None:
        from opentelemetry.instrumentation.pika import PikaInstrumentor
        from pika.spec import BasicProperties

        def publish_hook(span: Span, body: bytes, properties: BasicProperties) -> None:
            add_body_attribute(span, body, "messaging.publish.body")

        def consume_hook(span: Span, body: bytes, properties: BasicProperties) -> None:
            add_body_attribute(span, body, "messaging.consume.body")

        PikaInstrumentor().instrument(
            publish_hook=publish_hook,
            consume_hook=consume_hook,
        )


instrumentor: AbstractInstrumentor = PikaInstrumentor()
