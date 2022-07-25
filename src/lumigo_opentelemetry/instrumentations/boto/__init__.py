from lumigo_opentelemetry.instrumentations import AbstractInstrumentor

class BotoInstrumentor(AbstractInstrumentor):
    def __init__(self):
        super().__init__("boto")

    def get_otel_instrumentor(self):
        from opentelemetry.instrumentation.boto import (
            BotoInstrumentor as UpstreamInstrumentor,
        )

        return UpstreamInstrumentor()
