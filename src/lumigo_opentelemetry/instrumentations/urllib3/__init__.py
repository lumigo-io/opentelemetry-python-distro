from lumigo_opentelemetry.instrumentations import AbstractInstrumentor


class URLLib3Instrumentor(AbstractInstrumentor):
    def __init__(self):
        super().__init__("urllib3")

    def check_if_applicable(self):
        import urllib3  # noqa

    def install_instrumentation(self):
        from opentelemetry.instrumentation.urllib3 import URLLib3Instrumentor

        URLLib3Instrumentor().instrument()


instrumentor: AbstractInstrumentor = URLLib3Instrumentor()
