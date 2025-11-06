from typing import Dict, Union, List, Tuple, Any, Optional
import logging
from contextvars import ContextVar

from opentelemetry import context as otel_context


logger = logging.getLogger(__name__)
EXECUTION_TAG_KEY_PREFIX = "lumigo.execution_tags"
EXECUTION_TAGS_CONTEXT_KEY = "lumigo_execution_tags"
_EXECUTION_TAGS_TOKENS_STACK: ContextVar[Optional[List[Any]]] = ContextVar(
    "lumigo_execution_tags_tokens_stack",
    default=None,
)


def _get_execution_tags_token_stacks() -> List[Any]:
    stack: Optional[List[Any]] = _EXECUTION_TAGS_TOKENS_STACK.get()
    if stack is None:
        stack = []
        _EXECUTION_TAGS_TOKENS_STACK.set(stack)
    return stack


def _push_execution_tags_token(token: Any) -> None:
    _get_execution_tags_token_stacks().append(token)


def detach_execution_tags() -> None:
    """
    Detach all execution-tag contexts that were attached during this invocation.

    This prevents context leakage across warm invocations (e.g., AWS Lambda).
    """
    stack = _get_execution_tags_token_stacks()
    while stack:
        token = stack.pop()
        try:
            otel_context.detach(token)
        except Exception:
            logger.debug("Failed to detach execution tags context", exc_info=True)


def add_execution_tags(
    tags: Dict[str, Union[str, List[Any], Tuple[Any]]], only_current_span: bool = False
) -> None:
    """
    Add multiple execution tags that will be propagated to spans in the current invocation.

    By default, tags are propagated to all child spans of the same execution (process) using
    OpenTelemetry Context. When only_current_span=True, tags are only added to the current
    active span without propagation to child spans.

    Args:
        tags (Dict[str, Union[str, List, Tuple]]): Dictionary of execution tag key-value pairs
                                                  Values can be strings, lists, or tuples
        only_current_span (bool): If True, only add tags to current span.
                                 If False (default), propagate to all child spans.
    """
    if not isinstance(tags, dict):
        logger.error("Execution tags must be a dictionary")
        return

    valid_tags = _get_valid_tags(tags)

    if not valid_tags:
        logger.error("No valid execution tags to add")
        return

    if only_current_span:
        # Add tags only to the current active span
        from opentelemetry import trace

        current_span = trace.get_current_span()
        if current_span and current_span.is_recording():
            for key, value in valid_tags.items():
                span_attribute_key = f"{EXECUTION_TAG_KEY_PREFIX}.{key}"
                current_span.set_attribute(span_attribute_key, value)
        else:
            logger.warning("No active span to add execution tags to")
    else:
        # Add tags to context for propagation to all child spans (default behavior)
        current_tags = otel_context.get_value(EXECUTION_TAGS_CONTEXT_KEY) or {}

        updated_tags = current_tags.copy()
        updated_tags.update(valid_tags)

        # Set the updated tags in a new context and attach it; track token for proper detach
        new_context = otel_context.set_value(EXECUTION_TAGS_CONTEXT_KEY, updated_tags)
        token = otel_context.attach(new_context)
        _push_execution_tags_token(token)


def _get_valid_tags(
    tags: Dict[str, Union[str, List[Any], Tuple[Any]]]
) -> Dict[str, Union[str, List[Any]]]:
    valid_tags: Dict[str, Union[str, List[Any]]] = {}
    for key, value in tags.items():
        if not isinstance(key, str) or not key.strip():
            logger.error(
                f"Execution tag key must be a string and cannot be empty or whitespace: '{key}' (type: {type(key).__name__})"
            )
            continue

        if isinstance(value, str):
            if not value.strip():
                logger.error(
                    f"Empty or whitespace execution tag value: '{key}', '{value}'"
                )
                continue
            valid_tags[key] = value

        elif isinstance(value, (list, tuple)):
            if not value:  # Empty array/tuple
                logger.error(f"Empty array/tuple execution tag value: '{key}'")
                continue

            valid_tags[key] = list(value)
        else:
            valid_tags[key] = value
    return valid_tags
