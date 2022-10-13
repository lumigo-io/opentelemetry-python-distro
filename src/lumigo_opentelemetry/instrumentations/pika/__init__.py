from lumigo_opentelemetry.instrumentations import AbstractInstrumentor
from opentelemetry.instrumentation.instrumentor import BaseInstrumentor


class PikaInstrumentor(AbstractInstrumentor):
    def __init__(self) -> None:
        super().__init__("pika")

    def get_otel_instrumentor(self) -> BaseInstrumentor:
        from opentelemetry.instrumentation.pika import (
            PikaInstrumentor as UpstreamInstrumentor,
        )

        return UpstreamInstrumentor()
