from lumigo_opentelemetry.instrumentations import AbstractInstrumentor
from opentelemetry.instrumentation.instrumentor import BaseInstrumentor


class TornadoInstrumentor(AbstractInstrumentor):
    def __init__(self) -> None:
        super().__init__("tornado")

    def get_otel_instrumentor(self) -> BaseInstrumentor:
        from opentelemetry.instrumentation.tornado import (
            TornadoInstrumentor as UpstreamInstrumentor,
        )

        return UpstreamInstrumentor()
