from opentelemetry.sdk.trace import ReadableSpan, SpanProcessor
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace import Span, SpanKind

from lumigo_opentelemetry import logger
from lumigo_opentelemetry.libs.attributes import SKIP_EXPORT_SPAN_ATTRIBUTE
from lumigo_opentelemetry.utils.span_processor_utils import EXECUTION_TAG_KEY_PREFIX
from opentelemetry import context as otel_context
from lumigo_opentelemetry.utils.span_processor_utils import EXECUTION_TAGS_CONTEXT_KEY


class LumigoSpanProcessor(BatchSpanProcessor):
    def on_end(self, span: ReadableSpan) -> None:
        if should_skip_exporting_span(span):
            logger.debug("Not exporting span because it has NO_EXPORT=True attribute")
            return

        super().on_end(span)

        # If this is the root server span, force flush to ensure it is exported
        try:
            if (
                getattr(span, "kind", None) == SpanKind.SERVER
                and getattr(span, "parent", None) is None
            ):
                self.force_flush()
        except Exception:
            logger.warning("Failed to force flush at server root span end")


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


class LumigoExecutionTagProcessor(SpanProcessor):
    """
    Span processor that automatically adds execution tags from OpenTelemetry Context to all spans.

    This processor checks for execution tags stored in OpenTelemetry Context
    and adds them as attributes to spans when they start. It supports multiple
    execution tags as key-value pairs.
    """

    def on_start(self, span: Span, parent_context: None = None) -> None:
        """
        Called when a span starts. Adds all execution tags from context if present.

        Args:
            span: The span that is starting
            parent_context: The OpenTelemetry context to read execution tags from.
                Using the provided parent context avoids relying on the ambient
                current context and prevents context leakage across invocations.
        """
        try:
            # Read execution tags from the span's parent_context to avoid relying on ambient current context
            execution_tags = (
                otel_context.get_value(EXECUTION_TAGS_CONTEXT_KEY, parent_context) or {}
            )

            # Add each execution tag as a span attribute
            for tag_key, tag_value in execution_tags.items():
                span_attribute_key = f"{EXECUTION_TAG_KEY_PREFIX}.{tag_key}"
                # OpenTelemetry supports arrays/sequences as span attributes
                span.set_attribute(span_attribute_key, tag_value)

        except Exception as e:
            logger.debug(f"Failed to add execution tags to span: {e}")

    def force_flush(self, timeout_millis: int = 30000) -> bool:
        return True
