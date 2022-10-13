from lumigo_opentelemetry.instrumentations import AbstractInstrumentor
from opentelemetry.instrumentation.instrumentor import BaseInstrumentor


class PymemcacheInstrumentor(AbstractInstrumentor):
    def __init__(self) -> None:
        super().__init__("pymemcache")

    def get_otel_instrumentor(self) -> BaseInstrumentor:
        from opentelemetry.instrumentation.pymemcache import (
            PymemcacheInstrumentor as UpstreamInstrumentor,
        )

        return UpstreamInstrumentor()
