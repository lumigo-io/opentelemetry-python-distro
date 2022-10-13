from lumigo_opentelemetry.instrumentations import AbstractInstrumentor
from opentelemetry.instrumentation.instrumentor import BaseInstrumentor


class PymongoInstrumentor(AbstractInstrumentor):
    def __init__(self) -> None:
        super().__init__("pymongo")

    def get_otel_instrumentor(self) -> BaseInstrumentor:
        from opentelemetry.instrumentation.pymongo import (
            PymongoInstrumentor as UpstreamInstrumentor,
        )

        return UpstreamInstrumentor()
