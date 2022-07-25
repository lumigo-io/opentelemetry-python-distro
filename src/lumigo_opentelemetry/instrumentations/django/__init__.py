from lumigo_opentelemetry.instrumentations import AbstractInstrumentor

class DjangoInstrumentor(AbstractInstrumentor):
    def __init__(self):
        super().__init__("django")

    def get_otel_instrumentor(self):
        from opentelemetry.instrumentation.django import (
            DjangoInstrumentor as UpstreamInstrumentor,
        )

        return UpstreamInstrumentor()
