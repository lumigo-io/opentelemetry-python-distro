import pytest

from lumigo_opentelemetry.utils.config import (
    get_connection_timeout_seconds,
    get_disabled_instrumentations,
)


def test_get_connection_seconds_timeout_default():
    assert get_connection_timeout_seconds() == 3


@pytest.mark.parametrize(("str_val", "expected_val"), (["42", 42.0], ["3.14", 3.14]))
def test_get_connection_timeout_seconds_custom(str_val, expected_val, monkeypatch):
    monkeypatch.setenv("LUMIGO_CONNECTION_TIMEOUT", str_val)
    assert get_connection_timeout_seconds() == expected_val


def test_get_disabled_instrumentations_default():
    """Test default behavior when environment variable is not set"""
    assert get_disabled_instrumentations() == set()


def test_get_disabled_instrumentations_empty(monkeypatch):
    """Test behavior when environment variable is empty"""
    monkeypatch.setenv("LUMIGO_DISABLE_INSTRUMENTATION", "")
    assert get_disabled_instrumentations() == set()


def test_get_disabled_instrumentations_single(monkeypatch):
    """Test behavior with a single instrumentation"""
    monkeypatch.setenv("LUMIGO_DISABLE_INSTRUMENTATION", "boto")
    assert get_disabled_instrumentations() == {"boto"}


def test_get_disabled_instrumentations_multiple(monkeypatch):
    """Test behavior with multiple instrumentations"""
    monkeypatch.setenv("LUMIGO_DISABLE_INSTRUMENTATION", "boto,requests,redis")
    assert get_disabled_instrumentations() == {"boto", "requests", "redis"}


def test_get_disabled_instrumentations_with_spaces(monkeypatch):
    """Test behavior with spaces around instrumentation names"""
    monkeypatch.setenv("LUMIGO_DISABLE_INSTRUMENTATION", " boto , requests , redis ")
    assert get_disabled_instrumentations() == {"boto", "requests", "redis"}


def test_get_disabled_instrumentations_with_empty_values(monkeypatch):
    """Test behavior with empty values in the list"""
    monkeypatch.setenv("LUMIGO_DISABLE_INSTRUMENTATION", "boto,,requests,")
    assert get_disabled_instrumentations() == {"boto", "requests"}


def test_get_disabled_instrumentations_mixed_case(monkeypatch):
    """Test behavior with mixed case (should preserve original case)"""
    monkeypatch.setenv("LUMIGO_DISABLE_INSTRUMENTATION", "Boto,REQUESTS,Redis")
    assert get_disabled_instrumentations() == {"Boto", "REQUESTS", "Redis"}
