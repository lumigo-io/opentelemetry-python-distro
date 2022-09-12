from lumigo_opentelemetry.instrumentations import AbstractInstrumentor


class ElasticsearchInstrumentorWrapper(AbstractInstrumentor):
    def __init__(self) -> None:
        super().__init__("elasticsearch")

    def check_if_applicable(self) -> None:
        import elasticsearch  # noqa

    def install_instrumentation(self) -> None:
        from opentelemetry.instrumentation.elasticsearch import (
            ElasticsearchInstrumentor,
        )

        ElasticsearchInstrumentor().instrument()


instrumentor: AbstractInstrumentor = ElasticsearchInstrumentorWrapper()
