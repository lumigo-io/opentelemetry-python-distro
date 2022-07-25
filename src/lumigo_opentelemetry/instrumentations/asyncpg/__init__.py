from lumigo_opentelemetry.instrumentations import AbstractInstrumentor

class AsyncPGInstrumentor(AbstractInstrumentor):
    def __init__(self):
        super().__init__("asyncpg")

    def get_otel_instrumentor(self):
        from opentelemetry.instrumentation.aiopg import (
            AsyncPGInstrumentor as UpstreamInstrumentor,
        )

        return UpstreamInstrumentor()
