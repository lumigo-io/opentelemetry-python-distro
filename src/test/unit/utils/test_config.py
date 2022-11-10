import pytest

from lumigo_opentelemetry.utils.config import get_connection_timeout_seconds


def test_get_connection_seconds_timeout_default():
    assert get_connection_timeout_seconds() == 3


@pytest.mark.parametrize(("str_val", "expected_val"), (["42", 42.0], ["3.14", 3.14]))
def test_get_connection_timeout_seconds_custom(str_val, expected_val, monkeypatch):
    monkeypatch.setenv("LUMIGO_CONNECTION_TIMEOUT", str_val)
    assert get_connection_timeout_seconds() == expected_val
