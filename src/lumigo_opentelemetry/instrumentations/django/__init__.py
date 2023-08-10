from lumigo_opentelemetry.instrumentations import AbstractInstrumentor


class DjangoInstrumentorWrapper(AbstractInstrumentor):
    def __init__(self) -> None:
        super().__init__("django")

    def check_if_applicable(self) -> None:
        import django  # noqa

    def install_instrumentation(self) -> None:
        from opentelemetry.instrumentation.django import DjangoInstrumentor
        from lumigo_opentelemetry.instrumentations.django.parsers import DjangoUtil

        DjangoInstrumentor().instrument(request_hook=DjangoUtil.request_hook, response_hook=DjangoUtil.response_hook)


instrumentor: AbstractInstrumentor = DjangoInstrumentorWrapper()
