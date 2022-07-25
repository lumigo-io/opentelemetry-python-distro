from lumigo_opentelemetry.instrumentations import AbstractInstrumentor

class RedisInstrumentor(AbstractInstrumentor):
    def __init__(self) -> None:
        super().__init__("redis")

    def get_otel_instrumentor(self):
        from opentelemetry.instrumentation.redis import (
            RedisInstrumentor as UpstreamInstrumentor,
        )

        return UpstreamInstrumentor()
