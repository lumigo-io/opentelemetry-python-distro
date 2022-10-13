from lumigo_opentelemetry.instrumentations import AbstractInstrumentor
from opentelemetry.instrumentation.instrumentor import BaseInstrumentor


class AioHttpInstrumentor(AbstractInstrumentor):
    def __init__(self) -> None:
        super().__init__("aiohttp_client")

    def get_otel_instrumentor(self) -> BaseInstrumentor:
        from opentelemetry.instrumentation.aiohttp_client import (
            AioHttpClientInstrumentor as UpstreamInstrumentor,
        )

        return UpstreamInstrumentor()
