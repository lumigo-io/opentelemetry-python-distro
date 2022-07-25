from lumigo_opentelemetry.instrumentations import AbstractInstrumentor

class PymemcacheInstrumentor(AbstractInstrumentor):
    def __init__(self) -> None:
        super().__init__("pymemcache")

    def get_otel_instrumentor(self):
        from opentelemetry.instrumentation.pymemcache import (
            PymemcacheInstrumentor as UpstreamInstrumentor,
        )

        return UpstreamInstrumentor()
