from lumigo_opentelemetry.instrumentations import AbstractInstrumentor
from opentelemetry.instrumentation.instrumentor import BaseInstrumentor


class Psycopg2Instrumentor(AbstractInstrumentor):
    def __init__(self) -> None:
        super().__init__("psycopg2")

    def get_otel_instrumentor(self) -> BaseInstrumentor:
        from opentelemetry.instrumentation.psycopg2 import (
            Psycopg2Instrumentor as UpstreamInstrumentor,
        )

        return UpstreamInstrumentor()
