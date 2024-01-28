from __future__ import annotations

import json
from typing import Any, Dict, Optional, Type

from lumigo_core.triggers.event_trigger import parse_triggers
from opentelemetry.trace import Span

from lumigo_opentelemetry import logger
from lumigo_opentelemetry.libs.environment_variables import AUTO_FILTER_EMPTY_SQS
from lumigo_opentelemetry.libs.general_utils import (
    get_boolean_env_var,
    lumigo_safe_execute,
)
from lumigo_opentelemetry.libs.json_utils import dump_with_context
from lumigo_opentelemetry.resources.span_processor import set_span_skip_export
from lumigo_opentelemetry.utils.aws_utils import (
    extract_region_from_arn,
    get_resource_fullname,
)

from lumigo_opentelemetry.utils.span_utils import safe_get_span_attribute


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

    @classmethod
    def safe_extract_region(
        cls,
        span: Optional[Span] = None,
        service_name: Optional[str] = None,
        operation_name: Optional[str] = None,
        api_params: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        if span:
            try:
                region_from_attrs: Optional[str] = safe_get_span_attribute(
                    span=span, attribute_name="aws.region"
                )
                if region_from_attrs:
                    return region_from_attrs
            except Exception:
                pass

        # Try getting the region from the ARN
        try:
            arn = cls.safe_extract_arn(api_params=api_params)
            region_from_arn: Optional[str] = (
                extract_region_from_arn(arn=arn) if arn else None
            )
            if region_from_arn:
                return region_from_arn
        except Exception:
            pass

        return None

    @classmethod
    def safe_extract_url(
        cls,
        span: Optional[Span] = None,
        service_name: Optional[str] = None,
        operation_name: Optional[str] = None,
        api_params: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        try:
            region = cls.safe_extract_region(
                span=span,
                service_name=service_name,
                operation_name=operation_name,
                api_params=api_params,
            )
            if region and service_name:
                return f"https://{service_name.lower()}.{region}.amazonaws.com"
        except Exception:
            pass

        return None

    @classmethod
    def safe_extract_arn(
        cls,
        span: Optional[Span] = None,
        service_name: Optional[str] = None,
        operation_name: Optional[str] = None,
        api_params: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        # Child classes need to implement this, no generic implementation is possible
        return None

    @classmethod
    def safe_extract_resource_name(
        cls,
        span: Optional[Span] = None,
        service_name: Optional[str] = None,
        operation_name: Optional[str] = None,
        api_params: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        try:
            arn = cls.safe_extract_arn(api_params=api_params)
            return get_resource_fullname(arn) if arn else None
        except Exception:
            pass

        return None

    @classmethod
    def safe_extract_http_request_body(
        cls,
        span: Optional[Span] = None,
        service_name: Optional[str] = None,
        operation_name: Optional[str] = None,
        api_params: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        try:
            return dump_with_context("requestBody", api_params)  # type: ignore
        except Exception:
            pass

        return None

    @classmethod
    def _get_request_additional_attributes(
        cls,
        span: Span,
        service_name: str,
        operation_name: str,
        api_params: Dict[str, Any],
    ) -> Dict[str, Any]:
        attributes = {
            "aws.service": service_name,
            "http.method": operation_name,
        }
        request_body = cls.safe_extract_http_request_body(
            span=span,
            service_name=service_name,
            operation_name=operation_name,
            api_params=api_params,
        )
        if request_body:
            attributes["http.request.body"] = request_body

        region = AwsParser.safe_extract_region(
            span=span,
            service_name=service_name,
            operation_name=operation_name,
            api_params=api_params,
        )
        if region:
            attributes["region"] = region
        url = AwsParser.safe_extract_url(
            span=span,
            service_name=service_name,
            operation_name=operation_name,
            api_params=api_params,
        )
        if url:
            attributes["http.url"] = url

        resource_name = cls.safe_extract_resource_name(
            span=span,
            service_name=service_name,
            operation_name=operation_name,
            api_params=api_params,
        )
        if resource_name:
            attributes["aws.resource.name"] = resource_name

        return attributes

    @classmethod
    def parse_request(
        cls,
        span: Span,
        service_name: str,
        operation_name: str,
        api_params: Dict[str, Any],
    ) -> None:
        attributes = cls._get_request_additional_attributes(
            span=span,
            service_name=service_name,
            operation_name=operation_name,
            api_params=api_params,
        )
        span.set_attributes(attributes)

    @classmethod
    def request_hook(
        cls,
        span: Span,
        service_name: str,
        operation_name: str,
        api_params: Dict[str, Any],
    ) -> None:
        with lumigo_safe_execute("aws: request_hook"):
            parser = AwsParser.get_parser(service_name=service_name)
            parser.parse_request(
                span=span,
                service_name=service_name,
                operation_name=operation_name,
                api_params=api_params,
            )

    @classmethod
    def parse_response(
        cls, span: Span, service_name: str, operation_name: str, result: Dict[Any, Any]
    ) -> None:
        headers = result.get("ResponseMetadata", {}).get("HTTPHeaders", {})
        attributes = {
            "http.response.body": dump_with_context("responseBody", result),
            "http.response.headers": dump_with_context("responseHeaders", headers),
            "http.status_code": result.get("ResponseMetadata", {}).get(
                "HTTPStatusCode", ""
            ),
            "messageId": result.get("MessageId")
            or headers.get("x-amzn-requestid")
            or headers.get("x-amz-requestid", ""),
        }
        span.set_attributes(attributes)

    @classmethod
    def response_hook(
        cls, span: Span, service_name: str, operation_name: str, result: Dict[Any, Any]
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
    @classmethod
    def safe_extract_arn(
        cls,
        span: Optional[Span] = None,
        service_name: Optional[str] = None,
        operation_name: Optional[str] = None,
        api_params: Optional[Dict[Any, Any]] = None,
    ) -> Optional[str]:
        return api_params.get("TargetArn") if api_params else None

    @classmethod
    def safe_extract_http_request_body(
        cls,
        span: Optional[Span] = None,
        service_name: Optional[str] = None,
        operation_name: Optional[str] = None,
        api_params: Optional[Dict[Any, Any]] = None,
    ) -> Optional[str]:
        try:
            if api_params:
                return dump_with_context(  # type: ignore
                    "requestBody", api_params.get("Message", api_params or {})
                )
        except Exception:
            pass

        return None


class SqsParser(AwsParser):
    @staticmethod
    def extract_queue_name_from_url(queue_url: str) -> str:
        return queue_url.split("/")[-1]

    @classmethod
    def safe_extract_http_request_body(
        cls,
        span: Optional[Span] = None,
        service_name: Optional[str] = None,
        operation_name: Optional[str] = None,
        api_params: Optional[Dict[Any, Any]] = None,
    ) -> Optional[str]:
        try:
            if api_params:
                return dump_with_context(  # type: ignore
                    "requestBody", api_params.get("MessageBody", api_params or {})
                )
        except Exception:
            pass

        return None

    @classmethod
    def safe_extract_resource_name(
        cls,
        span: Optional[Span] = None,
        service_name: Optional[str] = None,
        operation_name: Optional[str] = None,
        api_params: Optional[Dict[Any, Any]] = None,
    ) -> Optional[str]:
        try:
            queue_url = cls.safe_extract_url(
                span=span,
                service_name=service_name,
                operation_name=operation_name,
                api_params=api_params,
            )
            resource_name = (
                cls.extract_queue_name_from_url(queue_url=queue_url)
                if queue_url
                else None
            )
            if resource_name:
                return resource_name
        except Exception:
            pass

        return None

    @staticmethod
    def _should_skip_empty_sqs_polling_response(
        operation_name: str, result: Dict[Any, Any]
    ) -> bool:
        """
        checks the sqs response & returns true if the request receive messages from SQS but no messages were returned
        """

        no_messages = not result or not result.get("Messages", None)
        sqs_poll = operation_name == "ReceiveMessage"
        return (
            sqs_poll
            and no_messages
            and get_boolean_env_var(AUTO_FILTER_EMPTY_SQS, True)
        )

    @classmethod
    def parse_response(
        cls, span: Span, service_name: str, operation_name: str, result: Dict[Any, Any]
    ) -> None:
        trigger_details = parse_triggers(
            {"service_name": service_name, "operation_name": operation_name, **result}
        )
        if trigger_details:
            span.set_attributes(
                {"lumigoData": json.dumps({"trigger": trigger_details})}
            )

        # Filter out sqs polls with empty response
        if cls._should_skip_empty_sqs_polling_response(operation_name, result):
            logger.debug(
                "Not tracing empty SQS polling requests "
                f"(override by setting the {AUTO_FILTER_EMPTY_SQS} env var to false)"
            )
            set_span_skip_export(span)


class LambdaParser(AwsParser):
    @classmethod
    def safe_extract_http_request_body(
        cls,
        span: Optional[Span] = None,
        service_name: Optional[str] = None,
        operation_name: Optional[str] = None,
        api_params: Optional[Dict[Any, Any]] = None,
    ) -> Optional[str]:
        try:
            if api_params:
                return dump_with_context(  # type: ignore
                    "requestBody", api_params.get("Payload", api_params or {})
                )
        except Exception:
            pass

        return None

    @classmethod
    def safe_extract_resource_name(
        cls,
        span: Optional[Span] = None,
        service_name: Optional[str] = None,
        operation_name: Optional[str] = None,
        api_params: Optional[Dict[str, str]] = None,
    ) -> Optional[str]:
        try:
            if api_params:
                resource_name = api_params.get("FunctionName")
                if resource_name:
                    return resource_name
        except Exception:
            pass

        return None


class DynamoParser(AwsParser):
    @classmethod
    def safe_extract_resource_name(
        cls,
        span: Optional[Span] = None,
        service_name: Optional[str] = None,
        operation_name: Optional[str] = None,
        api_params: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        try:
            if api_params:
                resource_name: Optional[str] = api_params.get("TableName")
                if resource_name:
                    return resource_name
        except Exception:
            pass

        return None

    @classmethod
    def _get_request_additional_attributes(
        cls,
        span: Span,
        service_name: str,
        operation_name: str,
        api_params: Dict[Any, Any],
    ) -> Dict[str, Any]:
        attributes = super()._get_request_additional_attributes(
            span=span,
            service_name=service_name,
            operation_name=operation_name,
            api_params=api_params,
        )
        attributes["aws.dynamodb.method"] = operation_name
        return attributes
