from typing import Dict, Any

from opentelemetry.trace import Span

from lumigo_wrapper.libs.general_utils import lumigo_safe_execute
from lumigo_wrapper.libs.json_utils import dump, safe_convert_bytes_to_string
from lumigo_wrapper.lumigo_utils import get_logger


class FastAPI:
    @staticmethod
    def is_fastapi(resource: Any) -> bool:
        try:
            import fastapi

            return isinstance(resource, fastapi.FastAPI)
        except ImportError:
            return False

    @staticmethod
    def instrument(resource: Any):
        if FastAPI.is_fastapi(resource=resource):
            try:
                from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

                FastAPIInstrumentor().instrument_app(
                    resource,
                    server_request_hook=FastAPIParser.server_request_hook,
                    client_request_hook=FastAPIParser.client_request_hook,
                    client_response_hook=FastAPIParser.client_response_hook,
                )
            except ImportError:
                pass


class FastAPIParser:
    @staticmethod
    def safe_extract_headers_bytes(headers: Any) -> Dict[str, str]:
        with lumigo_safe_execute("safe_extract_headers_bytes"):
            return {
                key.decode("utf-8"): value.decode("utf-8") for key, value in headers
            }
        return {}

    @staticmethod
    def server_request_hook(span: Span, scope: dict):
        with lumigo_safe_execute("FastAPIParser: server_request_hook"):
            headers = FastAPIParser.safe_extract_headers_bytes(
                headers=scope.get("headers", [])
            )
            query_string = scope.get("query_string", "")
            path = scope.get("path", "")
            attributes = {
                "http.request.headers": dump(headers),
                "http.request.query_string": dump(query_string),
                "http.request.path": dump(path),
            }
            span.set_attributes(attributes)

    @staticmethod
    def client_request_hook(span: Span, scope: dict):
        with lumigo_safe_execute("FastAPIParser: client_request_hook"):
            get_logger().debug(f"client_request_hook span: {span}, scope: {scope}")

    @staticmethod
    def client_response_hook(span: Span, message: dict):
        with lumigo_safe_execute("FastAPIParser: client_response_hook"):
            body = safe_convert_bytes_to_string(message.get("body"))
            if body:
                span.set_attribute("http.response.body", dump(body))
            headers = FastAPIParser.safe_extract_headers_bytes(
                headers=message.get("headers", [])
            )
            if headers:
                span.set_attribute("http.response.headers", dump(headers))
