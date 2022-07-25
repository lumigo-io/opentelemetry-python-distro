from lumigo_opentelemetry.instrumentations import AbstractInstrumentor

class PikaInstrumentor(AbstractInstrumentor):
    def __init__(self):
        super().__init__("pika")

    def get_otel_instrumentor(self):
        from opentelemetry.instrumentation.pika import (
            PikaInstrumentor as UpstreamInstrumentor,
        )

        return UpstreamInstrumentor()
