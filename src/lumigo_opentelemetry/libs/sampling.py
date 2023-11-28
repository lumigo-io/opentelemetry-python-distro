import os
import re
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

from lumigo_opentelemetry.libs.environment_variables import (
    AUTO_FILTER_HTTP_ENDPOINTS_REGEX,
)


class AttributeSampler(Sampler):
    """Sampler that returns a decision based on the provided attributes.

    Sampling takes place before request / response hooks are called, so our custom attributes are
    not yet available.

    By default, the decision is RECORD_AND_SAMPLE.

    If the AUTO_FILTER_HTTP_ENDPOINTS_REGEX environment variable is set, then the decision is based
    on whether the request URL matches the given regex. If it matches, then the decision is DROP.
    Otherwise, the decision is based on the parent span's decision.
    """

    def __init__(self) -> None:
        pass

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
        decision = Decision.RECORD_AND_SAMPLE
        attributes_url = _extract_url(attributes)
        if attributes_url and _should_skip_span_on_route_match(attributes_url):
            decision = Decision.DROP
            attributes = None

        return SamplingResult(
            decision,
            attributes,
            _get_parent_trace_state(parent_context),
        )

    def get_description(self) -> str:
        return "SkipSampler"


LUMIGO_SAMPLER = ParentBased(AttributeSampler())


def _extract_url(attributes: Attributes) -> Optional[str]:
    if attributes is not None:
        if "http.url" in attributes:
            return str(attributes["http.url"])
        url = ""
        if "http.host" in attributes:
            if "http.scheme" in attributes:
                url = f"{attributes['http.scheme']}://"

            if ":" in attributes["http.host"]:
                url += attributes["http.host"]
            else:
                url += attributes["http.host"]
                if "net.host.port" in attributes:
                    url += f":{attributes['net.host.port']}"

            if "http.target" in attributes:
                url += attributes["http.target"]
            else:
                if "http.route" in attributes:
                    url += attributes["http.route"]
                elif "http.path" in attributes:
                    url += attributes["http.path"]

            return url if len(url) > 0 else "/"

    return None


def _get_parent_trace_state(parent_context: "Context") -> Optional["TraceState"]:
    parent_span_context = get_current_span(parent_context).get_span_context()
    if parent_span_context is None or not parent_span_context.is_valid:
        return None
    return parent_span_context.trace_state


def _should_skip_span_on_route_match(url: Optional[str]) -> bool:
    """
    This function checks if the given route should be skipped from tracing.
    @param url: The complete url to check. Query params will be ignored.
    @return: True if the route should be skipped, False otherwise
    """
    if not url:
        return False
    url_without_query_params = url.split("?")[0]
    filter_regex_string = os.environ.get(AUTO_FILTER_HTTP_ENDPOINTS_REGEX, "")
    if not filter_regex_string:
        return False
    try:
        filter_regex = re.compile(filter_regex_string)
    except Exception:
        return False
    return filter_regex.search(url_without_query_params) is not None
