from lumigo_opentelemetry.instrumentations import AbstractInstrumentor


class PymongoInstrumentor(AbstractInstrumentor):
    def __init__(self):
        super().__init__("pymongo")

    def check_if_applicable(self):
        import pymongo  # noqa

    def install_instrumentation(self):
        from opentelemetry.instrumentation.pymongo import PymongoInstrumentor

        PymongoInstrumentor().instrument()


instrumentor: AbstractInstrumentor = PymongoInstrumentor()
