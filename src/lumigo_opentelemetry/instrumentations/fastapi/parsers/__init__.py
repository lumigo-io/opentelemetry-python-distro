from typing import Dict, Any

from lumigo_opentelemetry import logger
from lumigo_opentelemetry.libs.general_utils import lumigo_safe_execute
from lumigo_opentelemetry.libs.json_utils import dump, safe_convert_bytes_to_string

from opentelemetry.trace import Span


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
            logger.debug(f"client_request_hook span: {span}, scope: {scope}")

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
