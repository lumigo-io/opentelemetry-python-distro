from lumigo_opentelemetry.instrumentations import AbstractInstrumentor

class FalconInstrumentor(AbstractInstrumentor):
    def __init__(self):
        super().__init__("falcon")

    def get_otel_instrumentor(self):
        from opentelemetry.instrumentation.falcon import (
            FalconInstrumentor as UpstreamInstrumentor,
        )

        return UpstreamInstrumentor()
