from typing import Optional, Sequence

from opentelemetry.context import Context
from opentelemetry.sdk.trace.sampling import (
    Decision,
    ParentBased,
    Sampler,
    SamplingResult,
)
from opentelemetry.trace import Link, SpanKind, get_current_span
from opentelemetry.trace.span import TraceState
from opentelemetry.util.types import Attributes

from lumigo_opentelemetry.libs.attributes import SKIP_EXPORT_SPAN_ATTRIBUTE


class SkipSampler(Sampler):
    """Sampler that returns a decision based on the SKIP_EXPORT_SPAN_ATTRIBUTE attribute.

    If the SKIP_EXPORT_SPAN_ATTRIBUTE attribute exists and is set to True, the decision is DROP.
    Otherwise, the decision is RECORD_AND_SAMPLE. If the span in question has a parent, then the
    decision is based on the parent's decision.

    Technically, this is abuse of a sampler because it is not based on the a statistical sample,
    rather specific attributes of the root span.
    """

    def __init__(self) -> None:
        # default behavior is to record and sample
        self._decision = Decision.RECORD_AND_SAMPLE

    def should_sample(
        self,
        parent_context: Optional["Context"],
        trace_id: int,
        name: str,
        kind: SpanKind = None,
        attributes: Attributes = None,
        links: Optional[Sequence["Link"]] = None,
        trace_state: "TraceState" = None,
    ) -> "SamplingResult":
        # if SKIP_EXPORT_SPAN_ATTRIBUTE is in the attributes, then use that to determine the
        # decision
        if (
            attributes is not None
            and attributes.get(SKIP_EXPORT_SPAN_ATTRIBUTE, False) is True
        ):
            self._decision = Decision.DROP
            attributes = None
        return SamplingResult(
            self._decision,
            attributes,
            _get_parent_trace_state(parent_context),
        )

    def get_description(self) -> str:
        return "SkipSampler"


LUMIGO_SAMPLER = ParentBased(SkipSampler())


def _get_parent_trace_state(parent_context: "Context") -> Optional["TraceState"]:
    parent_span_context = get_current_span(parent_context).get_span_context()
    if parent_span_context is None or not parent_span_context.is_valid:
        return None
    return parent_span_context.trace_state
