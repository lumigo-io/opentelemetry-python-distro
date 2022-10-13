from lumigo_opentelemetry.instrumentations import AbstractInstrumentor
from opentelemetry.instrumentation.instrumentor import BaseInstrumentor


class HttpxInstrumentor(AbstractInstrumentor):
    def __init__(self) -> None:
        super().__init__("httpx")

    def get_otel_instrumentor(self) -> BaseInstrumentor:
        from opentelemetry.instrumentation.httpx import (
            HTTPXClientInstrumentor as UpstreamInstrumentor,
        )

        return UpstreamInstrumentor()
