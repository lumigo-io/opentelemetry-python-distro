import pytest
from opentelemetry.sdk.trace.sampling import Decision
from opentelemetry.trace import SpanKind

from lumigo_opentelemetry.libs.sampling import (
    _extract_endpoint,
    _get_string_list_from_env_var,
    does_search_regex_find_safe,
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
        sampler.should_sample(
            parent_context=None, trace_id=1, name="test", kind=spanKind
        ).decision
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
        # Make sure that the regex is searched and not matched
        ("word", "search for one word in this sentence", True),
        (".*word.*", "search for one word in this sentence", True),
        (r"^word$", "search for one word in this sentence", False),
        (
            r"^search for one word in this sentence$",
            "search for one word in this sentence",
            True,
        ),
        # This is an invalid regex, but we want to make sure it doesn't crash
        ("[", "", False),
        ("[", "[", False),
        # None values shouldn't crash the func
        (None, None, False),
        (None, "", False),
        ("", None, False),
    ],
)
def test_does_search_regex_find_safe(regex, value, should_match):
    assert does_search_regex_find_safe(regex, value) == should_match


@pytest.mark.parametrize(
    "env_var_name, env_var_value, expected_list",
    [
        ("LUMIGO_FILTER_HTTP_ENDPOINTS_REGEX", None, []),
        ("LUMIGO_FILTER_HTTP_ENDPOINTS_REGEX", "[]", []),
        ("LUMIGO_FILTER_HTTP_ENDPOINTS_REGEX", "[1,2,3]", []),
        ("LUMIGO_FILTER_HTTP_ENDPOINTS_REGEX", '["a","b","c"]', ["a", "b", "c"]),
        ("LUMIGO_FILTER_HTTP_ENDPOINTS_REGEX", '["a",1,"c"]', []),
        (
            "LUMIGO_FILTER_HTTP_ENDPOINTS_REGEX",
            r'["https:\\/\\/api\\.chucknorris\\.io\\/jokes\\/random"]',
            [r"https:\/\/api\.chucknorris\.io\/jokes\/random"],
        ),
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
            {"url.path": "/search", "http.target": "/about"},
            SpanKind.SERVER,
            "/search",
        ),
        ({"a": "a", "http.target": "/about"}, SpanKind.SERVER, "/about"),
        (
            {"url.full": "https://foo.bar/search", "http.url": "https://foo.bar/about"},
            SpanKind.CLIENT,
            "https://foo.bar/search",
        ),
        (
            {"a": "a", "http.url": "https://foo.bar/about"},
            SpanKind.CLIENT,
            "https://foo.bar/about",
        ),
        (
            {
                "url.path": "/search",
                "http.target": "/about",
                "url.full": "https://foo.bar/search",
                "http.url": "https://foo.bar/about",
            },
            SpanKind.INTERNAL,
            None,
        ),
        ({}, SpanKind.INTERNAL, None),
        ({}, SpanKind.SERVER, None),
        ({}, SpanKind.CLIENT, None),
        # If the client endpoint field is only a path, we return it as a path (best we can do)
        ({"http.url": "/about"}, SpanKind.CLIENT, "/about"),
        # If the server endpoint field is a full URL, we return only everything that comes after the path
        (
            {"http.url": "https://www.foo.bar/search?q=OpenTelemetry#SemConv"},
            SpanKind.SERVER,
            "/search?q=OpenTelemetry#SemConv",
        ),
    ],
)
def test_extract_endpoint(attributes, spanKind, expected_url):
    assert _extract_endpoint(attributes, spanKind) == expected_url
