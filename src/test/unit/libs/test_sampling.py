from lumigo_opentelemetry.libs.sampling import (
    _extract_url,
    _should_skip_span_on_route_match,
)


def test_extract_url():
    assert _extract_url({"http.url": "http://test.com"}) == "http://test.com"
    assert (
        _extract_url({"http.url": "http://test.com/test", "http.route": "/test"})
        == "http://test.com/test"
    )
    assert (
        _extract_url({"http.url": "http://test.com:8080/test", "http.route": "/test"})
        == "http://test.com:8080/test"
    )
    assert (
        _extract_url({"http.scheme": "http", "http.host": "test.com"})
        == "http://test.com/"
    )
    assert (
        _extract_url(
            {"http.scheme": "http", "http.host": "test.com", "http.route": "/test"}
        )
        == "http://test.com/test"
    )
    assert (
        _extract_url(
            {"http.scheme": "http", "http.host": "test.com:8080", "http.route": "/test"}
        )
        == "http://test.com:8080/test"
    )
    assert (
        _extract_url(
            {
                "http.scheme": "http",
                "http.host": "test.com:8080",
                "net.host.port": 8080,
                "http.route": "/test",
            }
        )
        == "http://test.com:8080/test"
    )
    assert (
        _extract_url(
            {
                "http.scheme": "http",
                "http.host": "test.com",
                "net.host.port": 8080,
                "http.route": "/test",
            }
        )
        == "http://test.com:8080/test"
    )
    assert _extract_url({"http.host": "test.com"}) == "test.com/"
    assert (
        _extract_url({"http.host": "test.com", "http.route": "/test"})
        == "test.com/test"
    )
    assert (
        _extract_url(
            {"http.host": "test.com", "net.host.port": 8080, "http.route": "/test"}
        )
        == "test.com:8080/test"
    )
    assert _extract_url({"http.target": "/test"}) == "/test"
    assert _extract_url({"http.target": "/test", "http.route": "/test"}) == "/test"
    assert _extract_url({"http.target": "/test", "http.path": "/test"}) == "/test"
    assert _extract_url({"http.route": "/test"}) == "/test"
    assert _extract_url({"http.route": "/test", "http.path": "/test"}) == "/test"
    assert _extract_url({"http.path": "/test"}) == "/test"
    assert _extract_url({}) is None


def test_should_skip_span_on_route_match(monkeypatch):
    monkeypatch.setenv("LUMIGO_AUTO_FILTER_HTTP_ENDPOINTS_REGEX", ".*(localhost).*/$")
    assert _should_skip_span_on_route_match("http://localhost:5000/") is True
    assert _should_skip_span_on_route_match("http://localhost:5000/unmatched") is False
    assert _should_skip_span_on_route_match("http://example.com:5000/") is False
    monkeypatch.setenv(
        "LUMIGO_AUTO_FILTER_HTTP_ENDPOINTS_REGEX", ".*(localhost).*/matched"
    )
    assert _should_skip_span_on_route_match("http://localhost:5000/matched") is True
    assert _should_skip_span_on_route_match("http://localhost:5000/unmatched") is False
    assert (
        _should_skip_span_on_route_match("http://example.com:5000/matched-incorrectly")
        is False
    )
    assert (
        _should_skip_span_on_route_match("http://localhost:5000/matched-incorrectly")
        is True
    )
