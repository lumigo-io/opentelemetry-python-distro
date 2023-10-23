from lumigo_opentelemetry.instrumentations import AbstractInstrumentor
from opentelemetry.trace import Span
from lumigo_opentelemetry.libs.general_utils import lumigo_safe_execute
from lumigo_opentelemetry.libs.json_utils import dump_with_context
from lumigo_opentelemetry.instrumentations.instrumentation_utils import (
    add_body_attribute,
)


class RequestsInstrumentor(AbstractInstrumentor):
    def __init__(self) -> None:
        super().__init__("requests")

    def check_if_applicable(self) -> None:
        from requests.models import Response  # noqa
        from requests.sessions import Session  # noqa
        from requests.structures import CaseInsensitiveDict  # noqa

    def install_instrumentation(self) -> None:
        from opentelemetry.instrumentation.requests import RequestsInstrumentor
        from requests.models import PreparedRequest, Response

        def request_hook(span: Span, request: PreparedRequest) -> None:
            with lumigo_safe_execute("requests request_hook"):
                span.set_attribute(
                    "http.request.headers",
                    dump_with_context("requestHeaders", request.headers),
                )
                add_body_attribute(span, request.body, "http.request.body")

        def response_hook(
            span: Span, request: PreparedRequest, response: Response
        ) -> None:
            with lumigo_safe_execute("requests response_hook"):
                span.set_attribute(
                    "http.response.headers",
                    dump_with_context("responseHeaders", response.headers),
                )
                add_body_attribute(span, response.content, "http.response.body")
                if "x-amzn-requestid" in response.headers:
                    span.set_attribute(
                        "messageId", response.headers["x-amzn-requestid"]
                    )

        RequestsInstrumentor().instrument(
            request_hook=request_hook, response_hook=response_hook
        )


instrumentor: AbstractInstrumentor = RequestsInstrumentor()
