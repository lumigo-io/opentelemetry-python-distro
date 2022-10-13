from lumigo_opentelemetry.instrumentations import AbstractInstrumentor
from opentelemetry.instrumentation.instrumentor import BaseInstrumentor


class URLLibInstrumentor(AbstractInstrumentor):
    def __init__(self) -> None:
        super().__init__("urllib")

    def get_otel_instrumentor(self) -> BaseInstrumentor:
        from opentelemetry.instrumentation.urllib import (
            URLLibInstrumentor as UpstreamInstrumentor,
        )

        return UpstreamInstrumentor()
