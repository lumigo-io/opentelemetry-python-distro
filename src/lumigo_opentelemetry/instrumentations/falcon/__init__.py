from lumigo_opentelemetry.instrumentations import AbstractInstrumentor
from opentelemetry.instrumentation.instrumentor import BaseInstrumentor


class FalconInstrumentor(AbstractInstrumentor):
    def __init__(self) -> None:
        super().__init__("falcon")

    def get_otel_instrumentor(self) -> BaseInstrumentor:
        from opentelemetry.instrumentation.falcon import (
            FalconInstrumentor as UpstreamInstrumentor,
        )

        return UpstreamInstrumentor()
