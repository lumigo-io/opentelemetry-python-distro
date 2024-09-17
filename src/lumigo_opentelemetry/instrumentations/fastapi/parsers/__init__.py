from typing import Any, Dict

from opentelemetry.trace import Span

from lumigo_opentelemetry.libs.general_utils import lumigo_safe_execute
from lumigo_opentelemetry.libs.json_utils import (
    dump,
    dump_with_context,
    safe_convert_bytes_to_string,
)


class FastAPIParser:
    @staticmethod
    def safe_extract_headers_bytes(headers: Any) -> Dict[str, str]:
        with lumigo_safe_execute("safe_extract_headers_bytes"):
            return {
                key.decode("utf-8"): value.decode("utf-8") for key, value in headers
            }
        return {}

    @staticmethod
    def server_request_hook(span: Span, scope: Dict[str, Any]) -> None:
        with lumigo_safe_execute("FastAPIParser: server_request_hook"):
            headers = FastAPIParser.safe_extract_headers_bytes(
                headers=scope.get("headers", [])
            )
            query_string = scope.get("query_string", "")
            path = scope.get("path", "")
            attributes = {
                "http.request.headers": dump_with_context("requestHeaders", headers),
                "http.request.query_string": dump(query_string),
                "http.request.path": dump(path),
            }
            span.set_attributes(attributes)

    @staticmethod
    def wrapt__get_otel_receive(original_func, instance, args, kwargs):  # type: ignore
        original_otel_receive = original_func(*args, **kwargs)

        async def new_otel_receive():  # type: ignore
            return_value = await original_otel_receive()
            with lumigo_safe_execute("FastAPIParser: new_otel_receive"):
                with instance.tracer.start_as_current_span("receive_body") as send_span:
                    send_span.set_attribute(
                        "http.request.body",
                        dump_with_context("requestBody", return_value),
                    )
            return return_value

        return new_otel_receive

    @staticmethod
    def client_response_hook(
        span: Span, scope: Dict[str, Any], message: Dict[str, Any]
    ) -> None:
        with lumigo_safe_execute("FastAPIParser: client_response_hook"):
            body = safe_convert_bytes_to_string(message.get("body"))
            if body:
                span.set_attribute(
                    "http.response.body", dump_with_context("responseBody", body)
                )
            headers = FastAPIParser.safe_extract_headers_bytes(
                headers=message.get("headers", [])
            )
            if headers:
                span.set_attribute(
                    "http.response.headers",
                    dump_with_context("responseHeaders", headers),
                )
