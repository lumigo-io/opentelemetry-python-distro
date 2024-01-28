from typing import Optional, Mapping, Any

from opentelemetry.trace import Span


def safe_get_span_attributes(span: Span) -> Optional[Mapping[str, Any]]:
    try:
        return (
            span.attributes
            if hasattr(span, "attributes") and isinstance(span.attributes, Mapping)
            else {}
        )
    except Exception:
        return None


def safe_get_span_attribute(span: Span, attribute_name: str) -> Optional[Any]:
    try:
        attributes = safe_get_span_attributes(span=span)
        return attributes.get(attribute_name) if attributes else None
    except Exception:
        return None
