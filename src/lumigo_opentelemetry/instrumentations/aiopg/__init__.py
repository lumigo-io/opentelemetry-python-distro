from lumigo_opentelemetry.instrumentations import AbstractInstrumentor
from opentelemetry.instrumentation.instrumentor import BaseInstrumentor


class AioPgInstrumentor(AbstractInstrumentor):
    def __init__(self) -> None:
        super().__init__("aiopg")

    def get_otel_instrumentor(self) -> BaseInstrumentor:
        from opentelemetry.instrumentation.aiopg import (
            AiopgInstrumentor as UpstreamInstrumentor,
        )

        return UpstreamInstrumentor()
