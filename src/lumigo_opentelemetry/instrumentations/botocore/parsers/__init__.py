from __future__ import annotations

from typing import Optional, Type, Dict, Any

from opentelemetry.trace import Span

from lumigo_opentelemetry.libs.general_utils import lumigo_safe_execute
from lumigo_opentelemetry.libs.json_utils import dump
from lumigo_opentelemetry.utils.aws_utils import (
    extract_region_from_arn,
    get_resource_fullname,
)


class AwsParser:
    @staticmethod
    def get_parser(
        service_name: str,
    ) -> Type[AwsParser]:
        parsers: Dict[str, Type[AwsParser]] = {
            "sns": SnsParser,
            "sqs": SqsParser,
            "lambda": LambdaParser,
            "dynamodb": DynamoParser,
        }
        return parsers.get(service_name, AwsParser)

    @staticmethod
    def parse_request(
        span: Span, service_name: str, operation_name: str, api_params: Dict[Any, Any]
    ) -> None:
        attributes = {
            "http.request.body": dump(api_params),
            "aws.service": service_name,
            "http.method": operation_name,
        }
        span.set_attributes(attributes)

    @staticmethod
    def request_hook(
        span: Span, service_name: str, operation_name: str, api_params: Dict[Any, Any]
    ) -> None:
        with lumigo_safe_execute("aws: request_hook"):
            parser = AwsParser.get_parser(service_name=service_name)
            parser.parse_request(
                span=span,
                service_name=service_name,
                operation_name=operation_name,
                api_params=api_params,
            )

    @staticmethod
    def parse_response(
        span: Span, service_name: str, operation_name: str, result: Dict[Any, Any]
    ) -> None:
        headers = result.get("ResponseMetadata", {}).get("HTTPHeaders", {})
        attributes = {
            "http.response.body": dump(result),
            "http.response.headers": dump(headers),
            "http.status_code": result.get("ResponseMetadata", {}).get(
                "HTTPStatusCode", ""
            ),
            "messageId": result.get("MessageId")
            or headers.get("x-amzn-requestid")
            or headers.get("x-amz-requestid", ""),
        }
        span.set_attributes(attributes)

    @staticmethod
    def response_hook(
        span: Span, service_name: str, operation_name: str, result: Dict[Any, Any]
    ) -> None:
        with lumigo_safe_execute("aws: response_hook"):
            parser = AwsParser.get_parser(service_name=service_name)
            parser.parse_response(
                span=span,
                service_name=service_name,
                operation_name=operation_name,
                result=result,
            )


class SnsParser(AwsParser):
    @staticmethod
    def safe_extract_arn(api_params: Dict[Any, Any]) -> Optional[str]:
        return api_params.get("TargetArn")

    @staticmethod
    def parse_request(
        span: Span, service_name: str, operation_name: str, api_params: Dict[Any, Any]
    ) -> None:
        arn = SnsParser.safe_extract_arn(api_params=api_params)
        region = extract_region_from_arn(arn=arn) if arn else None

        attributes = {
            "http.request.body": dump(api_params.get("Message", api_params or {})),
            "aws.service": service_name,
            "region": region or "",
            "http.method": operation_name,
            "http.url": f"https://{service_name.lower()}.{region}.amazonaws.com",
            "aws.resource.name": get_resource_fullname(arn) if arn else "",
        }
        span.set_attributes(attributes)


class SqsParser(AwsParser):
    @staticmethod
    def extract_queue_name_from_url(queue_url: str) -> str:
        return queue_url.split("/")[-1]

    @staticmethod
    def parse_request(
        span: Span, service_name: str, operation_name: str, api_params: Dict[Any, Any]
    ) -> None:
        queue_url = api_params.get("QueueUrl")
        resource_name = (
            SqsParser.extract_queue_name_from_url(queue_url=queue_url)
            if queue_url
            else None
        )
        attributes = {
            "http.request.body": dump(api_params.get("MessageBody", api_params or {})),
            "aws.service": service_name,
            "http.method": operation_name,
            "http.url": queue_url or "",
            "aws.resource.name": resource_name or "",
        }
        span.set_attributes(attributes)


class LambdaParser(AwsParser):
    @staticmethod
    def parse_request(
        span: Span, service_name: str, operation_name: str, api_params: Dict[Any, Any]
    ) -> None:
        resource_name = api_params.get("FunctionName")
        attributes = {
            "http.request.body": dump(api_params.get("Payload", api_params or {})),
            "aws.resource.name": resource_name or "",
            "aws.service": service_name,
            "http.method": operation_name,
        }
        span.set_attributes(attributes)


class DynamoParser(AwsParser):
    @staticmethod
    def parse_request(
        span: Span, service_name: str, operation_name: str, api_params: Dict[Any, Any]
    ) -> None:
        attributes = {
            "http.request.body": dump(api_params),
            "aws.service": service_name,
            "http.method": operation_name,
            "aws.resource.name": api_params.get("TableName", ""),
            "aws.dynamodb.method": operation_name,
        }
        span.set_attributes(attributes)
