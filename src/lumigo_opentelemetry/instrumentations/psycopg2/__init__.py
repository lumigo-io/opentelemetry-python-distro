from lumigo_opentelemetry.instrumentations import AbstractInstrumentor

class Psycopg2Instrumentor(AbstractInstrumentor):
    def __init__(self):
        super().__init__("psycopg2")

    def get_otel_instrumentor(self):
        from opentelemetry.instrumentation.psycopg2 import (
            Psycopg2Instrumentor as UpstreamInstrumentor,
        )

        return UpstreamInstrumentor()
