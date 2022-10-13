from lumigo_opentelemetry.instrumentations import AbstractInstrumentor
from opentelemetry.instrumentation.instrumentor import BaseInstrumentor


class PyMySqlInstrumentor(AbstractInstrumentor):
    def __init__(self) -> None:
        super().__init__("pymysql")

    def get_otel_instrumentor(self) -> BaseInstrumentor:
        from opentelemetry.instrumentation.pymysql import (
            PyMySQLInstrumentor as UpstreamInstrumentor,
        )

        return UpstreamInstrumentor()
