from lumigo_opentelemetry.instrumentations import AbstractInstrumentor
from opentelemetry.instrumentation.instrumentor import BaseInstrumentor


class BotoInstrumentor(AbstractInstrumentor):
    def __init__(self) -> None:
        super().__init__("boto")

    def get_otel_instrumentor(self) -> BaseInstrumentor:
        from opentelemetry.instrumentation.boto import (
            BotoInstrumentor as UpstreamInstrumentor,
        )

        return UpstreamInstrumentor()
