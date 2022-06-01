from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any
from requests import Response

from opentelemetry.trace import Span

from lumigo_opentelemetry.libs.general_utils import lumigo_safe_execute
from lumigo_opentelemetry.libs.json_utils import dump


@dataclass(frozen=True)
class HttpParser:
    response: Response

    @staticmethod
    def request_callback(span: Span, response: Response) -> None:
        with lumigo_safe_execute("HttpParser: request_callback"):
            if not response:
                return
            attributes = HttpParser.get_parser(response=response).get_attributes()

            span.set_attributes(attributes)

    def parse_request(self) -> Dict[str, Any]:
        request = self.response.request
        return {
            "http.request.body": dump(request.body),
            "http.request.headers": dump(request.headers),
        }

    def parse_response(self) -> Dict[str, Any]:
        return {
            "http.response.body": dump(self.response.text),
            "http.response.headers": dump(self.response.headers),
        }

    def extract_custom_attributes(self) -> Dict[str, Any]:
        return {}

    def get_attributes(self) -> Dict[str, Any]:
        return {
            **self.parse_request(),
            **self.parse_response(),
            **self.extract_custom_attributes(),
        }

    @staticmethod
    def get_parser(response: Response) -> HttpParser:
        url = response.url
        if url.endswith("amazonaws.com") or (
            response.request.headers
            and response.request.headers.get("x-amzn-requestid")
        ):
            return AwsParser(response=response)
        return HttpParser(response=response)


@dataclass(frozen=True)
class AwsParser(HttpParser):
    def extract_custom_attributes(self) -> Dict[str, Any]:
        with lumigo_safe_execute("aws: extract_custom_attributes"):
            return {
                "messageId": self.response.request.headers.get("x-amzn-requestid")
                if self.response.request
                else "",
            }
        return {}
