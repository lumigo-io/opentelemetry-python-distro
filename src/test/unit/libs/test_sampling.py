import pytest

from lumigo_opentelemetry.libs.sampling import (
    _extract_url,
    _should_skip_span_on_route_match,
)


@pytest.mark.parametrize(
    "attributes, expected_url",
    [
        ({"url.full": "http://test.com"}, "http://test.com"),
        ({"http.url": "http://test.com"}, "http://test.com"),
        (
            {"url.full": "http://test.com/test", "http.route": "/test"},
            "http://test.com/test",
        ),
        (
            {"http.url": "http://test.com/test", "http.route": "/test"},
            "http://test.com/test",
        ),
        (
            {"url.full": "http://test.com:8080/test", "http.route": "/test"},
            "http://test.com:8080/test",
        ),
        (
            {"http.url": "http://test.com:8080/test", "http.route": "/test"},
            "http://test.com:8080/test",
        ),
        ({"url.scheme": "http", "http.host": "test.com"}, "http://test.com/"),
        ({"http.scheme": "http", "http.host": "test.com"}, "http://test.com/"),
        (
            {"url.scheme": "http", "http.host": "test.com", "http.route": "/test"},
            "http://test.com/test",
        ),
        (
            {"http.scheme": "http", "http.host": "test.com", "http.route": "/test"},
            "http://test.com/test",
        ),
        (
            {
                "http.scheme": "http",
                "http.host": "test.com:8080",
                "http.route": "/test",
            },
            "http://test.com:8080/test",
        ),
        (
            {
                "http.scheme": "http",
                "http.host": "test.com:8080",
                "net.host.port": 8080,
                "http.route": "/test",
            },
            "http://test.com:8080/test",
        ),
        (
            {
                "http.scheme": "http",
                "http.host": "test.com",
                "net.host.port": 8080,
                "http.route": "/test",
            },
            "http://test.com:8080/test",
        ),
        ({"http.host": "test.com"}, "test.com/"),
        ({"http.host": "test.com", "http.route": "/test"}, "test.com/test"),
        (
            {"http.host": "test.com", "net.host.port": 8080, "http.route": "/test"},
            "test.com:8080/test",
        ),
        ({"http.target": "/test"}, "/test"),
        ({"http.target": "/test?a=b#hello"}, "/test?a=b#hello"),
        (
            {"url.path": "/test", "url.query": "a=b", "url.fragment": "hello"},
            "/test?a=b#hello",
        ),
        (
            {
                "url.path": "/test",
                "url.query": "a=b",
                "url.fragment": "hello",
                "http.target": "/test?a=b#hello",
                "http.route": "/test",
            },
            "/test?a=b#hello",
        ),
        ({"http.target": "/test?a=b#hello", "http.route": "/test"}, "/test?a=b#hello"),
        ({"http.target": "/test?a=b#hello", "http.path": "/test"}, "/test?a=b#hello"),
        ({"http.route": "/test"}, "/test"),
        ({"http.route": "/test", "http.path": "/test"}, "/test"),
        ({"http.path": "/test"}, "/test"),
        ({}, None),
    ],
)
def test_extract_url(attributes, expected_url):
    assert _extract_url(attributes) == expected_url


def test_should_skip_span_on_route_match(monkeypatch):
    monkeypatch.setenv("LUMIGO_AUTO_FILTER_HTTP_ENDPOINTS_REGEX", ".*(localhost).*/$")
    assert _should_skip_span_on_route_match("http://localhost:5000/") is True
    assert _should_skip_span_on_route_match("http://localhost:5000/?a=b") is False
    assert _should_skip_span_on_route_match("http://localhost:5000/unmatched") is False
    assert _should_skip_span_on_route_match("http://example.com:5000/") is False

    monkeypatch.setenv("LUMIGO_AUTO_FILTER_HTTP_ENDPOINTS_REGEX", ".*(localhost).*a=b")
    assert _should_skip_span_on_route_match("http://localhost:5000/") is False
    assert _should_skip_span_on_route_match("http://localhost:5000/?a=b") is True
    assert (
        _should_skip_span_on_route_match("http://localhost:5000/unmatched?c=d&a=b")
        is True
    )
    assert _should_skip_span_on_route_match("http://example.com:5000/") is False
    assert _should_skip_span_on_route_match("http://example.com:5000/?a=b&c=d") is False

    monkeypatch.setenv(
        "LUMIGO_AUTO_FILTER_HTTP_ENDPOINTS_REGEX", ".*(localhost).*/matched"
    )
    assert _should_skip_span_on_route_match("http://localhost:5000/matched") is True
    assert _should_skip_span_on_route_match("http://localhost:5000/matched?a=b") is True
    assert _should_skip_span_on_route_match("http://localhost:5000/unmatched") is False
    assert (
        _should_skip_span_on_route_match("http://example.com:5000/matched-incorrectly")
        is False
    )
    assert (
        _should_skip_span_on_route_match("http://localhost:5000/matched-incorrectly")
        is True
    )
