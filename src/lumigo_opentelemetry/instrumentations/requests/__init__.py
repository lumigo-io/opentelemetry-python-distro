from lumigo_opentelemetry.instrumentations import AbstractInstrumentor
from .parsers import HttpParser


class RequestsInstrumentor(AbstractInstrumentor):
    def __init__(self) -> None:
        super().__init__("requests")

    def check_if_applicable(self) -> None:
        from requests.models import Response  # noqa
        from requests.sessions import Session  # noqa
        from requests.structures import CaseInsensitiveDict  # noqa

    def install_instrumentation(self) -> None:
        from opentelemetry.instrumentation.requests import RequestsInstrumentor

        RequestsInstrumentor().instrument(span_callback=HttpParser.request_callback)


instrumentor: AbstractInstrumentor = RequestsInstrumentor()
