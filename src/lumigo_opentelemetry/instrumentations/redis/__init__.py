from lumigo_opentelemetry.instrumentations import AbstractInstrumentor
from opentelemetry.instrumentation.instrumentor import BaseInstrumentor


class RedisInstrumentor(AbstractInstrumentor):
    def __init__(self) -> None:
        super().__init__("redis")

    def get_otel_instrumentor(self) -> BaseInstrumentor:
        from opentelemetry.instrumentation.redis import (
            RedisInstrumentor as UpstreamInstrumentor,
        )

        return UpstreamInstrumentor()
