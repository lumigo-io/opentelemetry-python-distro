from unittest.mock import Mock, patch

import pytest

from lumigo_opentelemetry.resources.span_processor import (
    set_span_no_export,
    should_not_export_span,
    LumigoSpanProcessor,
)


def test_set_span_no_export():
    """
    Given a span, check that the span is marked as not exported
    """

    for no_export in [True, False]:
        span_mock = Mock(set_attribute=Mock())
        set_span_no_export(span_mock, no_export)
        (attributes,) = span_mock.set_attributes.call_args[0]
        assert attributes == {"NO_EXPORT": no_export}

    # Check default value
    span_mock = Mock(set_attribute=Mock())
    set_span_no_export(span_mock)
    (attributes,) = span_mock.set_attributes.call_args[0]
    assert attributes == {"NO_EXPORT": True}


@pytest.mark.parametrize(
    "attributes, should_export",
    [
        # Default is to export
        ({}, True),
        # Use the value if it is set
        ({"NO_EXPORT": False}, True),
        ({"NO_EXPORT": True}, False),
    ],
)
def test_should_not_export_span(attributes, should_export):
    readable_span_mock = Mock(attributes=attributes)

    assert should_not_export_span(readable_span_mock) is not should_export


@patch("lumigo_opentelemetry.resources.span_processor.should_not_export_span")
@patch("opentelemetry.sdk.trace.export.BatchSpanProcessor.on_end")
def test_lumigo_span_processor_no_export_set(
    mocked_super_on_end, mocked_should_not_export_span
):
    processor = LumigoSpanProcessor(Mock())
    readable_span_mock = Mock()
    mocked_should_not_export_span.return_value = True
    processor.on_end(span=readable_span_mock)

    # Check if the parent of processor BatchSpanProcessor.on_end not called
    mocked_super_on_end.assert_not_called()


@patch("lumigo_opentelemetry.resources.span_processor.should_not_export_span")
@patch("opentelemetry.sdk.trace.export.BatchSpanProcessor.on_end")
def test_lumigo_span_processor_no_export_not_set(
    mocked_super_on_end, mocked_should_not_export_span
):
    processor = LumigoSpanProcessor(Mock())
    readable_span_mock = Mock()

    # should_not_export is False. i.e. the span should be exported
    mocked_should_not_export_span.return_value = False
    processor.on_end(span=readable_span_mock)

    # Check if the parent of processor BatchSpanProcessor.on_end was called
    mocked_super_on_end.assert_called_once_with(readable_span_mock)
