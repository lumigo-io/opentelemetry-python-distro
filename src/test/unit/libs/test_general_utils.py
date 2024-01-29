import pytest

from lumigo_opentelemetry.libs.general_utils import (
    get_max_size,
    get_boolean_env_var,
    lumigo_safe_wrapper,
)


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


@pytest.mark.parametrize(
    "env_var_value,default,expected_result",
    [
        # Normal truth values
        ("true", False, True),
        ("True", False, True),
        ("TRUE", False, True),
        # Normal false values
        ("false", True, False),
        ("False", True, False),
        ("FALSE", True, False),
        # Invalid values, use the default
        ("RandomValue", False, False),
        ("RandomValue", True, True),
        # Empty values, use the default
        (None, False, False),
        (None, True, True),
    ],
)
def test_get_boolean_env_var(env_var_value, default, expected_result, monkeypatch):
    """Try getting a boolean value from env vars, and check all the different options work"""

    if env_var_value is not None:
        monkeypatch.setenv("TEST_VAR", env_var_value)
    assert get_boolean_env_var("TEST_VAR", default=default) is expected_result


def test_lumigo_safe_wrapper_happy_flow():
    @lumigo_safe_wrapper()
    def my_func():
        return 1

    assert my_func() == 1


def test_lumigo_safe_wrapper_exception():
    @lumigo_safe_wrapper()
    def my_func():
        raise Exception("test")

    assert my_func() is None


def test_lumigo_safe_wrapper_exception_default_value():
    @lumigo_safe_wrapper(default_return_value=1)
    def my_func():
        raise Exception("test")

    assert my_func() == 1
