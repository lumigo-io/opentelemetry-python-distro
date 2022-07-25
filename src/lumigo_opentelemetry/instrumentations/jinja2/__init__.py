from lumigo_opentelemetry.instrumentations import AbstractInstrumentor

class Jinja2Instrumentor(AbstractInstrumentor):
    def __init__(self):
        super().__init__("jinja2")

    def get_otel_instrumentor(self):
        from opentelemetry.instrumentation.jinja2 import (
            Jinja2Instrumentor as UpstreamInstrumentor,
        )

        return UpstreamInstrumentor()
