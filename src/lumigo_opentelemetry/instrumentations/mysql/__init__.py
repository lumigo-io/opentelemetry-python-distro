from lumigo_opentelemetry.instrumentations import AbstractInstrumentor
from opentelemetry.instrumentation.instrumentor import BaseInstrumentor


class MySqlInstrumentor(AbstractInstrumentor):
    def __init__(self) -> None:
        super().__init__("mysql")

    def get_otel_instrumentor(self) -> BaseInstrumentor:
        from opentelemetry.instrumentation.mysql import (
            MySQLInstrumentor as UpstreamInstrumentor,
        )

        return UpstreamInstrumentor()
