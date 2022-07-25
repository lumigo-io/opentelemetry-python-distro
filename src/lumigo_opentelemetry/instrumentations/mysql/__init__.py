from lumigo_opentelemetry.instrumentations import AbstractInstrumentor

class MySqlInstrumentor(AbstractInstrumentor):
    def __init__(self):
        super().__init__("mysql")

    def get_otel_instrumentor(self):
        from opentelemetry.instrumentation.mysql import (
            MySQLInstrumentor as UpstreamInstrumentor,
        )

        return UpstreamInstrumentor()
