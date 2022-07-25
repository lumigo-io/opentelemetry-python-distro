from lumigo_opentelemetry.instrumentations import AbstractInstrumentor

class PymongoInstrumentor(AbstractInstrumentor):
    def __init__(self) -> None:
        super().__init__("pymongo")

    def get_otel_instrumentor(self):
        from opentelemetry.instrumentation.pymongo import (
            PymongoInstrumentor as UpstreamInstrumentor,
        )

        return UpstreamInstrumentor()
