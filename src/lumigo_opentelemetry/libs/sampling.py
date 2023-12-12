import os
import re
from typing import Optional, Sequence
from urllib.parse import urlparse

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

from lumigo_opentelemetry import logger
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
            logger.debug(
                f"Dropping trace for url '{attributes_url}' because it matches the"
                f" auto-filter regex specified by '{AUTO_FILTER_HTTP_ENDPOINTS_REGEX}'"
            )
            decision = Decision.DROP
            attributes = None

        return SamplingResult(
            decision,
            attributes,
            _get_parent_trace_state(parent_context),
        )

    def get_description(self) -> str:
        return "SkipSampler"


_attribute_sampler = AttributeSampler()
LUMIGO_SAMPLER = ParentBased(
    root=_attribute_sampler,
    # If the parent was sampled we still want to check the current span for sampling
    remote_parent_sampled=_attribute_sampler,
    local_parent_sampled=_attribute_sampler,
)


def _extract_url(attributes: Attributes) -> Optional[str]:
    if attributes is None:
        return None

    raw_url = None
    # if the url is already in the attributes, return it
    if attributes.get("url.full"):
        raw_url = str(attributes["url.full"])
    elif attributes.get("http.url"):
        raw_url = str(attributes["http.url"])

    if not raw_url:
        # generate as much of the url as possible from the attributes

        # if we have the host and port, use them. it's even better if
        # we have the scheme as well
        host = ""
        if "http.host" in attributes:
            if "url.scheme" in attributes:
                host = f"{attributes['url.scheme']}://"
            elif "http.scheme" in attributes:
                host = f"{attributes['http.scheme']}://"

            if ":" in attributes["http.host"]:
                host += attributes["http.host"]
            else:
                host += attributes["http.host"]
                if "net.host.port" in attributes:
                    host += f":{attributes['net.host.port']}"

        path = ""

        # if we have the target, use it. otherwise, fallback to route
        # or path
        if "url.path" in attributes:
            path += attributes["url.path"]
            if "url.query" in attributes:
                path += f"?{attributes['url.query']}"
            if "url.fragment" in attributes:
                path += f"#{attributes['url.fragment']}"
        elif "http.target" in attributes:
            path += attributes["http.target"]
        elif "http.route" in attributes:
            path += attributes["http.route"]
        elif "http.path" in attributes:
            path += attributes["http.path"]

        # combine the host and path
        raw_url = host + path

    # If we still don't have a URL, return None
    if not raw_url:
        return None

    parsed_url = urlparse(raw_url)
    if (
        parsed_url.scheme not in ("http", "https")
        or not parsed_url.netloc
        or not parsed_url.hostname
    ):
        # We can't parse the URL, so return the raw URL
        return raw_url

    final_url = f"{parsed_url.scheme}://"
    final_url += (
        parsed_url.hostname
        if (parsed_url.netloc.endswith(":80") and parsed_url.scheme == "http")
        or (parsed_url.netloc.endswith(":443") and parsed_url.scheme == "https")
        else parsed_url.netloc
    )
    if parsed_url.path and parsed_url.path != "/":
        final_url += parsed_url.path
    if parsed_url.query:
        final_url += f"?{parsed_url.query}"
    return final_url


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
    filter_regex_string = os.environ.get(AUTO_FILTER_HTTP_ENDPOINTS_REGEX, "")
    if not filter_regex_string:
        return False
    try:
        filter_regex = re.compile(filter_regex_string)
    except Exception:
        logger.warning(
            f"Invalid regex in '{AUTO_FILTER_HTTP_ENDPOINTS_REGEX}': {filter_regex_string}",
            exc_info=True,
        )
        return False
    return filter_regex.search(url) is not None
