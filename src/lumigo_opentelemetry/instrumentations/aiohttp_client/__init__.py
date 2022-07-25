from lumigo_opentelemetry.instrumentations import AbstractInstrumentor

class AioHttpInstrumentor(AbstractInstrumentor):
    def __init__(self):
        super().__init__("aiohttp_client")

    def get_otel_instrumentor(self):
        from opentelemetry.instrumentation.aiohttp_client import (
            AioHttpClientInstrumentor as UpstreamInstrumentor,
        )

        return UpstreamInstrumentor()
