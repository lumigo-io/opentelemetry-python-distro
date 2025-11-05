from unittest.mock import MagicMock, patch
from lumigo_opentelemetry.instrumentations.langchain import (
    instrumentor as langchain_instrumentor,
)
from lumigo_opentelemetry.instrumentations.flask import (
    instrumentor as flask_instrumentor,
)
from lumigo_opentelemetry.instrumentations.boto import (
    instrumentor as boto_instrumentor,
)


def test_instrumentations_lambda_langchain_enabled():
    fake_langchain = MagicMock()
    with patch.dict("sys.modules", {"langchain": fake_langchain}):
        assert langchain_instrumentor.is_applicable() is True


def test_instrumentations_lambda_flask_enabled():
    flask_mock = MagicMock()
    with patch.dict("sys.modules", {"flask": flask_mock}):
        assert flask_instrumentor.is_applicable() is True


def test_instrumentation_disabled_via_env_var_single(monkeypatch):
    """Test that a single instrumentation can be disabled via LUMIGO_DISABLE_INSTRUMENTATION"""
    monkeypatch.setenv("LUMIGO_DISABLE_INSTRUMENTATION", "boto")
    fake_boto = MagicMock()
    with patch.dict("sys.modules", {"boto": fake_boto}):
        assert boto_instrumentor.is_applicable() is False


def test_instrumentation_disabled_via_env_var_multiple(monkeypatch):
    """Test that multiple instrumentations can be disabled via LUMIGO_DISABLE_INSTRUMENTATION"""
    monkeypatch.setenv("LUMIGO_DISABLE_INSTRUMENTATION", "boto,langchain")

    # Test boto is disabled
    fake_boto = MagicMock()
    with patch.dict("sys.modules", {"boto": fake_boto}):
        assert boto_instrumentor.is_applicable() is False

    # Test langchain is disabled
    fake_langchain = MagicMock()
    with patch.dict("sys.modules", {"langchain": fake_langchain}):
        assert langchain_instrumentor.is_applicable() is False


def test_instrumentation_disabled_via_env_var_with_spaces(monkeypatch):
    """Test that instrumentation names with spaces are handled correctly"""
    monkeypatch.setenv("LUMIGO_DISABLE_INSTRUMENTATION", " boto , langchain ")
    fake_boto = MagicMock()
    with patch.dict("sys.modules", {"boto": fake_boto}):
        assert boto_instrumentor.is_applicable() is False


def test_instrumentation_not_disabled_when_not_in_list(monkeypatch):
    """Test that instrumentations not in the disable list still work"""
    monkeypatch.setenv("LUMIGO_DISABLE_INSTRUMENTATION", "langchain")
    fake_boto = MagicMock()
    with patch.dict("sys.modules", {"boto": fake_boto}):
        assert boto_instrumentor.is_applicable() is True


def test_instrumentation_enabled_when_env_var_empty(monkeypatch):
    """Test that all instrumentations work when LUMIGO_DISABLE_INSTRUMENTATION is empty"""
    monkeypatch.setenv("LUMIGO_DISABLE_INSTRUMENTATION", "")
    fake_boto = MagicMock()
    with patch.dict("sys.modules", {"boto": fake_boto}):
        assert boto_instrumentor.is_applicable() is True


def test_instrumentation_disabled_takes_precedence_over_lambda_check(monkeypatch):
    """Test that LUMIGO_DISABLE_INSTRUMENTATION takes precedence over Lambda environment checks"""
    monkeypatch.setenv("LUMIGO_DISABLE_INSTRUMENTATION", "langchain")
    fake_langchain = MagicMock()
    with patch.dict("sys.modules", {"langchain": fake_langchain}):
        # langchain normally works on Lambda, but should be disabled by env var
        assert langchain_instrumentor.is_applicable() is False


def test_instrumentation_disabled_respects_case_sensitivity(monkeypatch):
    """Test that case sensitivity is respected in instrumentation names"""
    monkeypatch.setenv("LUMIGO_DISABLE_INSTRUMENTATION", "Boto")  # Capital B
    fake_boto = MagicMock()
    with patch.dict("sys.modules", {"boto": fake_boto}):
        # Should NOT be disabled because "Boto" != "boto"
        assert boto_instrumentor.is_applicable() is True
