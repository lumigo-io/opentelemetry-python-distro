from lumigo_opentelemetry.instrumentations import AbstractInstrumentor
from opentelemetry.instrumentation.instrumentor import BaseInstrumentor


class AsyncPGInstrumentor(AbstractInstrumentor):
    def __init__(self) -> None:
        super().__init__("asyncpg")

    def get_otel_instrumentor(self) -> BaseInstrumentor:
        from opentelemetry.instrumentation.aiopg import (
            AsyncPGInstrumentor as UpstreamInstrumentor,
        )

        return UpstreamInstrumentor()
