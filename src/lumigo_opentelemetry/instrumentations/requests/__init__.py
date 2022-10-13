from lumigo_opentelemetry.instrumentations import AbstractInstrumentor
from opentelemetry.instrumentation.instrumentor import BaseInstrumentor
from .parsers import HttpParser


class RequestsInstrumentor(AbstractInstrumentor):
    def __init__(self) -> None:
        super().__init__("requests")

    def get_otel_instrumentor(self) -> BaseInstrumentor:
        from opentelemetry.instrumentation.requests import (
            RequestsInstrumentor as UpstreamInstrumentor,
        )

        return UpstreamInstrumentor()

    def _do_instrument(self, instrumentor):
        instrumentor.instrument(span_callback=HttpParser.request_callback)
