from unittest.mock import Mock

from opentelemetry.trace import Span

from lumigo_opentelemetry.instrumentations.instrumentation_utils import (
    add_body_attribute,
    PAYLOAD_MAX_SIZE,
)


def test_add_body_attribute_happy_flow():
    span_mock = Mock(Span)
    add_body_attribute(span_mock, "body", "attribute")
    assert len(span_mock.set_attribute.call_args_list) == 1
    assert span_mock.set_attribute.call_args_list[0][0] == ("attribute", "body")


def test_add_body_attribute_unicode():
    span_mock = Mock(Span)
    add_body_attribute(span_mock, "body".encode(), "attribute")
    assert len(span_mock.set_attribute.call_args_list) == 1
    assert span_mock.set_attribute.call_args_list[0][0] == ("attribute", "body")


def test_add_body_attribute_non_utf8_binary():
    span_mock = Mock(Span)
    add_body_attribute(span_mock, b"\x80\x81\x82", "attribute")
    assert len(span_mock.set_attribute.call_args_list) == 1
    assert span_mock.set_attribute.call_args_list[0][0] == ("attribute", "0x808182")


def test_add_body_attribute_exception():
    span_mock = Mock(Span)
    span_mock.set_attribute.side_effect = Exception("test")
    add_body_attribute(span_mock, "body", "attribute")
    # No exception should be raised


def test_add_body_attribute_too_long():
    span_mock = Mock(Span)
    add_body_attribute(span_mock, "a" * PAYLOAD_MAX_SIZE * 2, "attribute")
    assert len(span_mock.set_attribute.call_args_list) == 1
    assert span_mock.set_attribute.call_args_list[0][0] == (
        "attribute",
        "a" * PAYLOAD_MAX_SIZE,
    )


def test_add_body_attribute_non_string_or_bytes():
    span_mock = Mock(Span)
    add_body_attribute(span_mock, None, "attribute")
    assert len(span_mock.set_attribute.call_args_list) == 1
    assert span_mock.set_attribute.call_args_list[0][0] == ("attribute", "None")
