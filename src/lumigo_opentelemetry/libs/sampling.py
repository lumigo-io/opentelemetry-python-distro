import json
import os
import re
from typing import Optional, Sequence, List, Mapping, Any

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
from urllib.parse import urlparse, ParseResult

from lumigo_opentelemetry import logger
from lumigo_opentelemetry.libs.environment_variables import (
    LUMIGO_FILTER_HTTP_ENDPOINTS_REGEX,
    LUMIGO_FILTER_HTTP_ENDPOINTS_REGEX_CLIENT,
    LUMIGO_FILTER_HTTP_ENDPOINTS_REGEX_SERVER,
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
        if not should_sample(attributes, kind):
            decision = Decision.DROP
            attributes = None

        return SamplingResult(
            decision,
            attributes,
            _get_parent_trace_state(parent_context),
        )

    def get_description(self) -> str:
        return "SkipSampler"


def should_sample(attributes: Mapping[str, Any], span_kind: SpanKind) -> bool:
    endpoint = _extract_endpoint(attributes, span_kind)
    if endpoint:
        if (
            span_kind == SpanKind.SERVER
            and does_endpoint_match_server_filtering_regexes(endpoint)
        ):
            logger.debug(
                f"Dropping trace for endpoint '{endpoint}' because it matches one of the"
                f" filter regexes specified by the '{LUMIGO_FILTER_HTTP_ENDPOINTS_REGEX_SERVER}' env var"
            )
            return False
        elif (
            span_kind == SpanKind.CLIENT
            and does_endpoint_match_client_filtering_regexes(endpoint)
        ):
            logger.debug(
                f"Dropping trace for endpoint '{endpoint}' because it matches one of the"
                f" filter regexes specified by the '{LUMIGO_FILTER_HTTP_ENDPOINTS_REGEX_CLIENT}' env var"
            )
            return False
        elif does_endpoint_match_filtering_regexes(endpoint):
            logger.debug(
                f"Dropping trace for endpoint '{endpoint}' because it matches one of the"
                f" filter regexes specified by the '{LUMIGO_FILTER_HTTP_ENDPOINTS_REGEX}' env var"
            )
            return False

    return True


_attribute_sampler = AttributeSampler()
LUMIGO_SAMPLER = ParentBased(
    root=_attribute_sampler,
    # If the parent was sampled we still want to check the current span for sampling
    remote_parent_sampled=_attribute_sampler,
    local_parent_sampled=_attribute_sampler,
)


def does_endpoint_match_env_var_filtering_regex(
    endpoint: str, env_var_name: str
) -> bool:
    regexes = _get_string_list_from_env_var(env_var_name)
    if not regexes:
        return False

    return any(does_search_regex_find_safe(regex, endpoint) for regex in regexes)


def does_endpoint_match_client_filtering_regexes(endpoint: str) -> bool:
    return does_endpoint_match_env_var_filtering_regex(
        endpoint, LUMIGO_FILTER_HTTP_ENDPOINTS_REGEX_CLIENT
    )


def does_endpoint_match_server_filtering_regexes(endpoint: str) -> bool:
    return does_endpoint_match_env_var_filtering_regex(
        endpoint, LUMIGO_FILTER_HTTP_ENDPOINTS_REGEX_SERVER
    )


def does_endpoint_match_filtering_regexes(endpoint: str) -> bool:
    return does_endpoint_match_env_var_filtering_regex(
        endpoint, LUMIGO_FILTER_HTTP_ENDPOINTS_REGEX
    )


def does_search_regex_find_safe(regex: str, value: str) -> bool:
    if not regex or value is None:
        return False

    try:
        return re.search(regex, value) is not None
    except Exception:
        logger.warning(f"Invalid regex: {regex}")
        return False


def _get_string_list_from_env_var(env_var_name: str) -> List[str]:
    env_var_value = os.environ.get(env_var_name)
    if not env_var_value:
        return []

    parsed_list = None
    try:
        parsed_list = json.loads(env_var_value)
    except Exception:
        pass

    if (
        parsed_list is None
        or not isinstance(parsed_list, list)
        or any(not isinstance(item, str) for item in parsed_list)
    ):
        logger.warning(
            f"The value of env var '{env_var_name}' is not valid JSON format for an array of strings: {env_var_value}"
        )
        return []

    return parsed_list


def _extract_endpoint(attributes: Attributes, spanKind: SpanKind) -> Optional[str]:
    """
    Extract the endpoint from the given span attributes.

    Expected attributes for HTTP CLIENT spans:
    * url.full - The Absolute URL describing a network resource. E.g. "https://www.foo.bar/search?q=OpenTelemetry#SemConv"

    Expected attributes for HTTP SERVER spans:
    * url.path - The URI path component. E.g. "/search"

    Deprecated attributes (see https://opentelemetry.io/docs/specs/semconv/attributes-registry/http/#deprecated-http-attributes):
    * http.target - replaced by the url.path & url.query attributes. Example: "/search?q=OpenTelemetry#SemConv"
    * http.url - replaced by the url.full attribute. Example: "https://www.foo.bar/search?q=OpenTelemetry#SemConv"
    """
    if attributes is None:
        return None

    endpoint = None
    if spanKind == SpanKind.CLIENT:
        endpoint = (
            attributes.get("url.full")
            or attributes.get("http.url")
            or attributes.get("http.target")
        )
    elif spanKind == SpanKind.SERVER:
        endpoint = (
            attributes.get("url.path")
            or attributes.get("http.target")
            or attributes.get("http.url")
        )

    endpoint = str(endpoint) if endpoint else None

    if not endpoint:
        return None

    parsed_endpoint: ParseResult = urlparse(endpoint)
    if spanKind == SpanKind.CLIENT:
        return parsed_endpoint.geturl()
    elif spanKind == SpanKind.SERVER:
        # Make sure that we only return the path and everything that comes after it, not the full URL
        return ParseResult(
            scheme="",
            netloc="",
            path=parsed_endpoint.path,
            params=parsed_endpoint.params,
            query=parsed_endpoint.query,
            fragment=parsed_endpoint.fragment,
        ).geturl()

    return None


def _get_parent_trace_state(parent_context: "Context") -> Optional["TraceState"]:
    parent_span_context = get_current_span(parent_context).get_span_context()
    if parent_span_context is None or not parent_span_context.is_valid:
        return None
    return parent_span_context.trace_state
