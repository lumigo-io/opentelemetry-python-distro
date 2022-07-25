from lumigo_opentelemetry.instrumentations import AbstractInstrumentor

class PyramidInstrumentor(AbstractInstrumentor):
    def __init__(self) -> None:
        super().__init__("pyramid")

    def get_otel_instrumentor(self):
        from opentelemetry.instrumentation.pyramid import (
            PyramidInstrumentor as UpstreamInstrumentor,
        )

        return UpstreamInstrumentor()
