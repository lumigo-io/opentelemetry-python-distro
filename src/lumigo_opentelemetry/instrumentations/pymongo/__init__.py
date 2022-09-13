from lumigo_opentelemetry.instrumentations import AbstractInstrumentor


class PymongoInstrumentor(AbstractInstrumentor):
    def __init__(self) -> None:
        super().__init__("pymongo")

    def check_if_applicable(self) -> None:
        import pymongo  # noqa

    def install_instrumentation(self) -> None:
        from opentelemetry.instrumentation.pymongo import PymongoInstrumentor

        PymongoInstrumentor().instrument()


instrumentor: AbstractInstrumentor = PymongoInstrumentor()
