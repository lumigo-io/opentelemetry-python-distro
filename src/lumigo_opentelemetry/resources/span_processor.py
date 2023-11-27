from opentelemetry.sdk.trace import ReadableSpan
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace import Span

from lumigo_opentelemetry import logger
from lumigo_opentelemetry.libs.attributes import SKIP_EXPORT_SPAN_ATTRIBUTE


class LumigoSpanProcessor(BatchSpanProcessor):
    def on_end(self, span: ReadableSpan) -> None:
        if should_skip_exporting_span(span):
            logger.debug("Not exporting span because it has NO_EXPORT=True attribute")
            return

        super().on_end(span)


def should_skip_exporting_span(span: ReadableSpan) -> bool:
    """
    Given a span, returns an answer if the span should be exported or not.
    @param span: A readable span to check
    @return: True if the span should not be exported, False otherwise
    """
    return span.attributes.get(SKIP_EXPORT_SPAN_ATTRIBUTE, False) is True


def set_span_skip_export(span: Span, skip_export: bool = True) -> None:
    """
    marks the span as a span not intended for export (for example in spans that create a lot of noise and customers
    do not want to trace)

    @param span: The span to mark (The span is altered in place)
    @param skip_export: Should the span be exported or not (default is True, the span will not be exported)
    @return:
    """

    span.set_attributes({SKIP_EXPORT_SPAN_ATTRIBUTE: skip_export})
