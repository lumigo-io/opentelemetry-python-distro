from lumigo_opentelemetry.instrumentations import AbstractInstrumentor

class ElasticsearchInstrumentor(AbstractInstrumentor):
    def __init__(self):
        super().__init__("elasticsearch")

    def get_otel_instrumentor(self):
        from opentelemetry.instrumentation.elasticsearch import (
            ElasticsearchInstrumentor as UpstreamInstrumentor,
        )

        return UpstreamInstrumentor()
