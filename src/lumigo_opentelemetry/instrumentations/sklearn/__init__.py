from lumigo_opentelemetry.instrumentations import AbstractInstrumentor
from opentelemetry.instrumentation.instrumentor import BaseInstrumentor


class SklearnInstrumentor(AbstractInstrumentor):
    def __init__(self) -> None:
        super().__init__("sklearn")

    def get_otel_instrumentor(self) -> BaseInstrumentor:
        from opentelemetry.instrumentation.sklearn import (
            SklearnInstrumentor as UpstreamInstrumentor,
        )

        return UpstreamInstrumentor()
