from unittest.mock import MagicMock, patch
from lumigo_opentelemetry.instrumentations.langchain import (
    instrumentor as langchain_instrumentor,
)
from lumigo_opentelemetry.instrumentations.flask import (
    instrumentor as flask_instrumentor,
)


def test_instrumentations_lambda_langchain_enabled():
    fake_langchain = MagicMock()
    with patch.dict("sys.modules", {"langchain": fake_langchain}):
        assert langchain_instrumentor.is_applicable() is True


def test_instrumentations_lambda_flask_enabled():
    flask_mock = MagicMock()
    with patch.dict("sys.modules", {"flask": flask_mock}):
        assert flask_instrumentor.is_applicable() is True


def test_instrumentations_lambda_flask_disabled_on_lambda(monkeypatch):
    monkeypatch.setenv("AWS_LAMBDA_FUNCTION_NAME", "true")
    flask_mock = MagicMock()
    with patch.dict("sys.modules", {"flask": flask_mock}):
        assert flask_instrumentor.is_applicable() is False
