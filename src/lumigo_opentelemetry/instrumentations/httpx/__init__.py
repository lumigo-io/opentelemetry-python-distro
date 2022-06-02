from lumigo_opentelemetry.instrumentations import AbstractInstrumentor


class HttpxInstrumentorWrapper(AbstractInstrumentor):
    def __init__(self):
        super().__init__("httpx")

    def check_if_applicable(self):
        import httpx  # noqa

    def install_instrumentation(self):
        from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

        HTTPXClientInstrumentor().instrument()


instrumentor: AbstractInstrumentor = HttpxInstrumentorWrapper()
