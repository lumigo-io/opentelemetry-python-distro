from lumigo_opentelemetry.libs.json_utils import (
    dump,
)


def test_lumigo_dumps_max_size_span_attr_env_var_is_set(monkeypatch):
    monkeypatch.setenv("OTEL_SPAN_ATTRIBUTE_VALUE_LENGTH_LIMIT", "1")
    assert dump({None: 1}) == "{...[too long]"


def test_lumigo_dumps_max_size_otel_attr_env_var_is_set(monkeypatch):
    monkeypatch.setenv("OTEL_ATTRIBUTE_VALUE_LENGTH_LIMIT", "3")
    assert dump({"key": "b"}) == '{"k...[too long]'


def test_lumigo_dumps_default_max_size(monkeypatch):
    assert dump({"name": "test_1"}) == '{"name": "test_1"}'
