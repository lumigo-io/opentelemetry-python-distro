from lumigo_opentelemetry.instrumentations import AbstractInstrumentor
from opentelemetry.instrumentation.instrumentor import BaseInstrumentor


class KafkaInstrumentor(AbstractInstrumentor):
    def __init__(self) -> None:
        super().__init__("kafka")

    def get_otel_instrumentor(self) -> BaseInstrumentor:
        from opentelemetry.instrumentation.kafka import (
            KafkaInstrumentor as UpstreamInstrumentor,
        )

        return UpstreamInstrumentor()
