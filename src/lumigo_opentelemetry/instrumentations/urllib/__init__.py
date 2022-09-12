from lumigo_opentelemetry.instrumentations import AbstractInstrumentor


class URLLibInstrumentor(AbstractInstrumentor):
    def __init__(self) -> None:
        super().__init__("urllib")

    def check_if_applicable(self) -> None:
        import urllib  # noqa

    def install_instrumentation(self) -> None:
        from opentelemetry.instrumentation.urllib import URLLibInstrumentor

        URLLibInstrumentor().instrument()


instrumentor: AbstractInstrumentor = URLLibInstrumentor()
