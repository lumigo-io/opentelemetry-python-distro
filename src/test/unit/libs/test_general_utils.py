from lumigo_opentelemetry.libs.general_utils import get_max_size


def test_get_max_size_otel_span_attr_limit_is_set(monkeypatch):
    monkeypatch.setenv("OTEL_SPAN_ATTRIBUTE_VALUE_LENGTH_LIMIT", "3")
    assert get_max_size() == 3


def test_get_max_size_otel_attr_limit_is_set(monkeypatch):
    monkeypatch.setenv("OTEL_ATTRIBUTE_VALUE_LENGTH_LIMIT", "20")
    assert get_max_size() == 20


def test_get_max_size_both_env_vars_are_set(monkeypatch):
    monkeypatch.setenv("OTEL_SPAN_ATTRIBUTE_VALUE_LENGTH_LIMIT", "3")
    monkeypatch.setenv("OTEL_ATTRIBUTE_VALUE_LENGTH_LIMIT", "20")
    assert get_max_size() == 3


def test_get_max_size_get_default_value():
    assert get_max_size() == 2048
