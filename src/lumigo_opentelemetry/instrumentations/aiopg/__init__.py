from lumigo_opentelemetry.instrumentations import AbstractInstrumentor

class AioPgInstrumentor(AbstractInstrumentor):
    def __init__(self):
        super().__init__("aiopg")

    def get_otel_instrumentor(self):
        from opentelemetry.instrumentation.aiopg import (
            AiopgInstrumentor as UpstreamInstrumentor,
        )

        return UpstreamInstrumentor()
