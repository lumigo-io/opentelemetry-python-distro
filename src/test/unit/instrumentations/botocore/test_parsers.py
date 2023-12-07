import logging

import pytest
from unittest.mock import Mock, patch

from lumigo_opentelemetry.instrumentations.botocore.parsers import SqsParser


EMPTY_SQS_RESULT_1 = {}
EMPTY_SQS_RESULT_2 = {"Messages": []}
NON_EMPTY_SQS_RESULT = {"Messages": [{"MessageId": "1234", "Body": "test"}]}


@pytest.mark.parametrize(
    "env_var_value, operation, result, should_skip",
    [
        # Check that empty sqs polls are skipped
        ("true", "ReceiveMessage", EMPTY_SQS_RESULT_1, True),
        ("true", "ReceiveMessage", EMPTY_SQS_RESULT_2, True),
        # Check that non-empty polls are not skipped
        ("true", "ReceiveMessage", NON_EMPTY_SQS_RESULT, False),
        # Check that other operations are not skipped
        ("true", "DeleteMessage", EMPTY_SQS_RESULT_1, False),
        ("true", "DeleteMessageBatch", EMPTY_SQS_RESULT_1, False),
        ("true", "SendMessage", EMPTY_SQS_RESULT_1, False),
        ("true", "SendMessageBatch", EMPTY_SQS_RESULT_1, False),
        ("true", "UnknownOperation", EMPTY_SQS_RESULT_1, False),
        ("true", None, EMPTY_SQS_RESULT_1, False),
        # Check that empty sqs polls are not skipped if the env var is set to false
        ("false", "ReceiveMessage", EMPTY_SQS_RESULT_1, False),
        ("false", "ReceiveMessage", EMPTY_SQS_RESULT_2, False),
        # Check that non-empty polls are not skipped if the env var is set to false
        ("false", "ReceiveMessage", NON_EMPTY_SQS_RESULT, False),
        # Check that the default behavior is to skip empty sqs polls
        (None, "ReceiveMessage", EMPTY_SQS_RESULT_1, True),
        (None, "ReceiveMessage", EMPTY_SQS_RESULT_2, True),
        ("UnsupportedEnvVarValue", "ReceiveMessage", EMPTY_SQS_RESULT_2, True),
    ],
)
def test_sqs_skip_sqs_response(
    env_var_value, operation, result, should_skip, monkeypatch
):
    if env_var_value is not None:
        monkeypatch.setenv("LUMIGO_AUTO_FILTER_EMPTY_SQS", env_var_value)

    assert (
        SqsParser._should_skip_empty_sqs_polling_response(operation, result)
        == should_skip
    )


@patch(
    "lumigo_opentelemetry.instrumentations.botocore.parsers.SqsParser._should_skip_empty_sqs_polling_response"
)
def test_parse_sqs_response_skipping_empty_polls_outputs_log(
    should_skip_mock, caplog, monkeypatch
):
    monkeypatch.setenv("LUMIGO_DEBUG", "true")
    should_skip_mock.return_value = True
    span = Mock(set_attribute=Mock())
    service_name = "sqs"
    operation_name = "ReceiveMessage"
    result = {
        "ResponseMetadata": {
            "RequestId": "54bf0dab-cfab-5fa5-b284-50d83403c94c",
            "HTTPStatusCode": 200,
            "HTTPHeaders": {
                "x-amzn-requestid": "54bf0dab-cfab-5fa5-b284-50d83403c94c",
                "date": "Thu, 07 Sep 2023 16:25:12 GMT",
                "content-type": "text/xml",
                "content-length": "240",
                "connection": "keep-alive",
            },
            "RetryAttempts": 0,
        }
    }

    with caplog.at_level(logging.INFO):
        SqsParser.parse_response(span, service_name, operation_name, result)

        assert "not tracing empty sqs polling requests" in caplog.text.lower()


@patch(
    "lumigo_opentelemetry.instrumentations.botocore.parsers.SqsParser._should_skip_empty_sqs_polling_response"
)
def test_parse_sqs_response_not_skipping_polls_no_output_log(should_skip_mock, caplog):
    should_skip_mock.return_value = False
    span = Mock(set_attribute=Mock())
    service_name = "sqs"
    operation_name = "ReceiveMessage"
    result = {
        "ResponseMetadata": {
            "RequestId": "54bf0dab-cfab-5fa5-b284-50d83403c94c",
            "HTTPStatusCode": 200,
            "HTTPHeaders": {
                "x-amzn-requestid": "54bf0dab-cfab-5fa5-b284-50d83403c94c",
                "date": "Thu, 07 Sep 2023 16:25:12 GMT",
                "content-type": "text/xml",
                "content-length": "240",
                "connection": "keep-alive",
            },
            "RetryAttempts": 0,
        }
    }

    SqsParser.parse_response(span, service_name, operation_name, result)

    assert "not tracing empty sqs polling requests" not in caplog.text.lower()

    # Make sure that there is an info log
