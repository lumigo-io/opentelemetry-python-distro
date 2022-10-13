from lumigo_opentelemetry.instrumentations import AbstractInstrumentor
from opentelemetry.instrumentation.instrumentor import BaseInstrumentor


class PyramidInstrumentor(AbstractInstrumentor):
    def __init__(self) -> None:
        super().__init__("pyramid")

    def get_otel_instrumentor(self) -> BaseInstrumentor:
        from opentelemetry.instrumentation.pyramid import (
            PyramidInstrumentor as UpstreamInstrumentor,
        )

        return UpstreamInstrumentor()
