from lumigo_opentelemetry.instrumentations import AbstractInstrumentor

class HttpxInstrumentor(AbstractInstrumentor):
    def __init__(self):
        super().__init__("httpx")

    def get_otel_instrumentor(self):
        from opentelemetry.instrumentation.httpx import (
            HTTPXClientInstrumentor as UpstreamInstrumentor,
        )

        return UpstreamInstrumentor()
