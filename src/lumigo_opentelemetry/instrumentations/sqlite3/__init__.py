from lumigo_opentelemetry.instrumentations import AbstractInstrumentor

class SQLite3Instrumentor(AbstractInstrumentor):
    def __init__(self) -> None:
        super().__init__("sqlite3")

    def get_otel_instrumentor(self):
        from opentelemetry.instrumentation.sqlite3 import (
            SQLite3Instrumentor as UpstreamInstrumentor,
        )

        return UpstreamInstrumentor()
