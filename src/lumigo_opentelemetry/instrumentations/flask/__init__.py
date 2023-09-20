from typing import Any, Dict

from opentelemetry.trace.span import Span

from lumigo_opentelemetry.instrumentations import AbstractInstrumentor
from lumigo_opentelemetry.libs.general_utils import lumigo_safe_execute
from lumigo_opentelemetry.libs.json_utils import dump_with_context


class FlaskInstrumentorWrapper(AbstractInstrumentor):
    def __init__(self) -> None:
        super().__init__("flask")

    def check_if_applicable(self) -> None:
        import flask  # noqa

    def install_instrumentation(self) -> None:
        from opentelemetry.instrumentation.flask import FlaskInstrumentor

        def request_hook(span: Span, flask_request_environ: Dict[str, Any]) -> None:
            with lumigo_safe_execute("flask_request_hook"):
                span.set_attribute(
                    "http.request.headers",
                    dump_with_context("requestHeaders", flask_request_environ),
                )

        def response_hook(
            span: Span, status: int, response_headers: Dict[str, Any]
        ) -> None:
            with lumigo_safe_execute("flask_response_hook"):
                span.set_attribute(
                    "http.response.headers",
                    dump_with_context("responseHeaders", response_headers),
                )

        FlaskInstrumentor().instrument(
            request_hook=request_hook, response_hook=response_hook
        )


instrumentor: AbstractInstrumentor = FlaskInstrumentorWrapper()
