from lumigo_opentelemetry.instrumentations import AbstractInstrumentor
from opentelemetry.instrumentation.instrumentor import BaseInstrumentor


class Jinja2Instrumentor(AbstractInstrumentor):
    def __init__(self) -> None:
        super().__init__("jinja2")

    def get_otel_instrumentor(self) -> BaseInstrumentor:
        from opentelemetry.instrumentation.jinja2 import (
            Jinja2Instrumentor as UpstreamInstrumentor,
        )

        return UpstreamInstrumentor()
