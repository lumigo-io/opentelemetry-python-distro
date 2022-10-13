from lumigo_opentelemetry.instrumentations import AbstractInstrumentor
from opentelemetry.instrumentation.instrumentor import BaseInstrumentor


class ElasticsearchInstrumentor(AbstractInstrumentor):
    def __init__(self) -> None:
        super().__init__("elasticsearch")

    def get_otel_instrumentor(self) -> BaseInstrumentor:
        from opentelemetry.instrumentation.elasticsearch import (
            ElasticsearchInstrumentor as UpstreamInstrumentor,
        )

        return UpstreamInstrumentor()
