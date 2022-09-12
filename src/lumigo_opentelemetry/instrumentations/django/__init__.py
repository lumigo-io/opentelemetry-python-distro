from lumigo_opentelemetry.instrumentations import AbstractInstrumentor


class DjangoInstrumentorWrapper(AbstractInstrumentor):
    def __init__(self) -> None:
        super().__init__("django")

    def check_if_applicable(self) -> None:
        import django  # noqa

    def install_instrumentation(self) -> None:
        from opentelemetry.instrumentation.django import DjangoInstrumentor

        DjangoInstrumentor().instrument()


instrumentor: AbstractInstrumentor = DjangoInstrumentorWrapper()
