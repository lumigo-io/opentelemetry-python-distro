import pytest
from opentelemetry.sdk.trace.sampling import Decision
from opentelemetry.trace import SpanKind

from lumigo_opentelemetry.libs.sampling import (
    _extract_endpoint,
    _get_string_list_from_env_var,
    does_match_regex_safe,
    does_endpoint_match_filtering_regexes,
    AttributeSampler,
)


@pytest.mark.parametrize(
    "endpoint, spanKind, matches_server_filter, matched_client_filter, matched_general_filter, expected_sampling_decision",
    [
        ("/orders", SpanKind.SERVER, True, False, False, Decision.DROP),
        ("/orders", SpanKind.SERVER, False, True, False, Decision.RECORD_AND_SAMPLE),
        ("/orders", SpanKind.SERVER, False, False, True, Decision.DROP),
        (
            "https://foo.bar",
            SpanKind.CLIENT,
            True,
            False,
            False,
            Decision.RECORD_AND_SAMPLE,
        ),
        ("https://foo.bar", SpanKind.CLIENT, False, True, False, Decision.DROP),
        ("https://foo.bar", SpanKind.CLIENT, False, False, True, Decision.DROP),
    ],
)
def test_should_sample(
    endpoint,
    spanKind,
    matches_server_filter,
    matched_client_filter,
    matched_general_filter,
    expected_sampling_decision,
    monkeypatch,
):
    monkeypatch.setattr(
        "lumigo_opentelemetry.libs.sampling._extract_endpoint",
        lambda *args, **kwargs: endpoint,
    )
    monkeypatch.setattr(
        "lumigo_opentelemetry.libs.sampling.does_endpoint_match_server_filtering_regexes",
        lambda *args, **kwargs: matches_server_filter,
    )
    monkeypatch.setattr(
        "lumigo_opentelemetry.libs.sampling.does_endpoint_match_client_filtering_regexes",
        lambda *args, **kwargs: matched_client_filter,
    )
    monkeypatch.setattr(
        "lumigo_opentelemetry.libs.sampling.does_endpoint_match_filtering_regexes",
        lambda *args, **kwargs: matched_general_filter,
    )
    sampler = AttributeSampler()
    assert (
        sampler.should_sample(trace_id=1, name="test", kind=spanKind).decision
        == expected_sampling_decision
    )


@pytest.mark.parametrize(
    "endpoint, env_var_name, env_var_value, should_match",
    [
        ("/orders", "LUMIGO_FILTER_HTTP_ENDPOINTS_REGEX", '[".*orders.*"]', True),
        ("/orders", "LUMIGO_FILTER_HTTP_ENDPOINTS_REGEX", '[".*no-match.*"]', False),
    ],
)
def test_does_endpoint_match_filtering_regexes(
    endpoint, env_var_name, env_var_value, should_match, monkeypatch
):
    monkeypatch.setenv(env_var_name, env_var_value)
    assert does_endpoint_match_filtering_regexes(endpoint) == should_match


@pytest.mark.parametrize(
    "regex, value, should_match",
    [
        ("", "", False),
        ("", "a", False),
        ("a", "", False),
        ("a", "a", True),
        ("a", "b", False),
        # This is an invalid regex, but we want to make sure it doesn't crash
        ("[", "", False),
        ("[", "[", False),
        # None values shouldn't crash the func
        (None, None, False),
        (None, "", False),
        ("", None, False),
    ],
)
def test_does_match_regex_safe(regex, value, should_match):
    assert does_match_regex_safe(regex, value) == should_match


@pytest.mark.parametrize(
    "env_var_name, env_var_value, expected_list",
    [
        ("LUMIGO_FILTER_HTTP_ENDPOINTS_REGEX", None, []),
        ("LUMIGO_FILTER_HTTP_ENDPOINTS_REGEX", "[]", []),
        ("LUMIGO_FILTER_HTTP_ENDPOINTS_REGEX", "[1,2,3]", []),
        ("LUMIGO_FILTER_HTTP_ENDPOINTS_REGEX", '["a","b","c"]', ["a", "b", "c"]),
        ("LUMIGO_FILTER_HTTP_ENDPOINTS_REGEX", '["a",1,"c"]', []),
    ],
)
def test_extract_string_list_from_env_var(
    env_var_name, env_var_value, expected_list, monkeypatch
):
    monkeypatch.setenv(env_var_name, env_var_value)
    assert _get_string_list_from_env_var(env_var_name) == expected_list


@pytest.mark.parametrize(
    "attributes, spanKind, expected_url",
    [
        (
            {"url.path": "urlPath", "http.target": "httpTarget"},
            SpanKind.SERVER,
            "urlPath",
        ),
        ({"a": "a", "http.target": "httpTarget"}, SpanKind.SERVER, "httpTarget"),
        ({"url.full": "fullUrl", "http.url": "httpUrl"}, SpanKind.CLIENT, "fullUrl"),
        ({"a": "a", "http.url": "httpUrl"}, SpanKind.CLIENT, "httpUrl"),
        (
            {
                "url.path": "urlPath",
                "http.target": "httpTarget",
                "url.full": "fullUrl",
                "http.url": "httpUrl",
            },
            SpanKind.INTERNAL,
            None,
        ),
        ({}, SpanKind.INTERNAL, None),
        ({}, SpanKind.SERVER, None),
        ({}, SpanKind.CLIENT, None),
    ],
)
def test_extract_endpoint(attributes, spanKind, expected_url):
    assert _extract_endpoint(attributes, spanKind) == expected_url


# def test_should_skip_span_on_route_match(monkeypatch):
#     monkeypatch.setenv("LUMIGO_AUTO_FILTER_HTTP_ENDPOINTS_REGEX", ".*(localhost).*/$")
#     assert _should_skip_span_on_route_match("http://localhost:5000/") is True
#     assert _should_skip_span_on_route_match("http://localhost:5000/?a=b") is False
#     assert _should_skip_span_on_route_match("http://localhost:5000/unmatched") is False
#     assert _should_skip_span_on_route_match("http://example.com:5000/") is False
#
#     monkeypatch.setenv("LUMIGO_AUTO_FILTER_HTTP_ENDPOINTS_REGEX", ".*(localhost).*a=b")
#     assert _should_skip_span_on_route_match("http://localhost:5000/") is False
#     assert _should_skip_span_on_route_match("http://localhost:5000/?a=b") is True
#     assert (
#         _should_skip_span_on_route_match("http://localhost:5000/unmatched?c=d&a=b")
#         is True
#     )
#     assert _should_skip_span_on_route_match("http://example.com:5000/") is False
#     assert _should_skip_span_on_route_match("http://example.com:5000/?a=b&c=d") is False
#
#     monkeypatch.setenv(
#         "LUMIGO_AUTO_FILTER_HTTP_ENDPOINTS_REGEX", ".*(localhost).*/matched"
#     )
#     assert _should_skip_span_on_route_match("http://localhost:5000/matched") is True
#     assert _should_skip_span_on_route_match("http://localhost:5000/matched?a=b") is True
#     assert _should_skip_span_on_route_match("http://localhost:5000/unmatched") is False
#     assert (
#         _should_skip_span_on_route_match("http://example.com:5000/matched-incorrectly")
#         is False
#     )
#     assert (
#         _should_skip_span_on_route_match("http://localhost:5000/matched-incorrectly")
#         is True
#     )
