from lumigo_opentelemetry.instrumentations import AbstractInstrumentor
from opentelemetry.instrumentation.instrumentor import BaseInstrumentor


class DjangoInstrumentor(AbstractInstrumentor):
    def __init__(self) -> None:
        super().__init__("django")

    def get_otel_instrumentor(self) -> BaseInstrumentor:
        from opentelemetry.instrumentation.django import (
            DjangoInstrumentor as UpstreamInstrumentor,
        )

        return UpstreamInstrumentor()
