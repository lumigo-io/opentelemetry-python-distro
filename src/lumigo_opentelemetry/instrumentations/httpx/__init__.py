from lumigo_opentelemetry.instrumentations import AbstractInstrumentor
from opentelemetry.trace import Span
from lumigo_opentelemetry.libs.general_utils import lumigo_safe_execute
from lumigo_opentelemetry.libs.json_utils import dump_with_context
from lumigo_opentelemetry.instrumentations.instrumentation_utils import (
    add_body_attribute,
)
from typing import Tuple, Any


class HttpxInstrumentorWrapper(AbstractInstrumentor):
    def __init__(self) -> None:
        super().__init__("httpx")

    def is_disabled_on_lambda(self) -> bool:
        return False

    def assert_instrumented_package_importable(self) -> None:
        import httpx  # noqa

    def install_instrumentation(self) -> None:
        from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
        import httpx

        def request_hook(span: Span, request: Tuple[Any, ...]) -> Tuple[Any, ...]:
            with lumigo_safe_execute("requests request_hook"):
                method, url, headers, stream, extensions = request
                body = b"".join([chunk for chunk in stream])
                span.set_attribute(
                    "http.request.headers",
                    dump_with_context("requestHeaders", dict(headers)),
                )
                add_body_attribute(span, body, "http.request.body")
                request = (method, url, headers, httpx.ByteStream(body), extensions)
                return request

        async def async_request_hook(
            span: Span, request: Tuple[Any, ...]
        ) -> Tuple[Any, ...]:
            return request_hook(span, request)

        def response_hook(
            span: Span, request: Tuple[Any, ...], response: Tuple[Any, ...]
        ) -> None:
            with lumigo_safe_execute("requests response_hook"):
                status_code, headers, stream, extensions = response
                span.set_attribute(
                    "http.response.headers",
                    dump_with_context("responseHeaders", dict(headers)),
                )
                if "x-amzn-requestid" in headers:
                    span.set_attribute("messageId", headers["x-amzn-requestid"])

        async def async_response_hook(
            span: Span, request: Tuple[Any, ...], response: Tuple[Any, ...]
        ) -> None:
            return response_hook(span, request, response)

        HTTPXClientInstrumentor().instrument(
            request_hook=request_hook,
            response_hook=response_hook,
            async_request_hook=async_request_hook,
            async_response_hook=async_response_hook,
        )


instrumentor: AbstractInstrumentor = HttpxInstrumentorWrapper()
