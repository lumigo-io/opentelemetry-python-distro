from lumigo_opentelemetry.instrumentations import AbstractInstrumentor

class KafkaInstrumentor(AbstractInstrumentor):
    def __init__(self):
        super().__init__("kafka")

    def get_otel_instrumentor(self):
        from opentelemetry.instrumentation.kafka import (
            KafkaInstrumentor as UpstreamInstrumentor,
        )

        return UpstreamInstrumentor()
