from opentelemetry.trace import Span
from opentelemetry.sdk.trace import ReadableSpan
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from lumigo_opentelemetry import logger


class LumigoSpanProcessor(BatchSpanProcessor):
    def on_end(self, span: ReadableSpan) -> None:
        if should_not_export_span(span):
            logger.debug("Not exporting span because it has NO_EXPORT=True attribute")
            return

        super().on_end(span)


def should_not_export_span(span: ReadableSpan) -> bool:
    """
    Given a span, returns an answer if the span should be exported or not.
    @param span: A readable span to check
    @return: True if the span should not be exported, False otherwise
    """
    return span.attributes.get("NO_EXPORT") is True


def set_span_no_export(span: Span, no_export: bool = True) -> None:
    """
    marks the span as a span not intended for export (for example in spans that create a lot of noise and customers
    do not want to trace)

    @param span: The span to mark (The span is altered in place)
    @param no_export: Should the span be exported or not (default is True, the span will not be exported)
    @return:
    """

    span.set_attributes({"NO_EXPORT": no_export})
