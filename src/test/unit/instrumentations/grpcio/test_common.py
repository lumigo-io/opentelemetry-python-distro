from unittest.mock import Mock

from lumigo_opentelemetry.instrumentations.grpcio.common import (
    add_payload_in_bulks,
    PAYLOAD_MAX_SIZE,
)


def test_add_payload_in_bulks(monkeypatch):
    add_payload = add_payload_in_bulks("test.attr")

    span_mock = Mock(set_attribute=Mock())
    monkeypatch.setattr(
        "lumigo_opentelemetry.instrumentations.grpcio.common.get_current_span",
        lambda: span_mock,
    )
    add_payload("payload1")
    add_payload("payload2")

    assert span_mock.set_attribute.call_args[0] == ("test.attr", "payload1,payload2")


def test_add_payload_in_bulks_too_big(monkeypatch):
    add_payload = add_payload_in_bulks("test.attr")

    span_mock = Mock(set_attribute=Mock())
    monkeypatch.setattr(
        "lumigo_opentelemetry.instrumentations.grpcio.common.get_current_span",
        lambda: span_mock,
    )
    add_payload("test1")
    add_payload("test2" * PAYLOAD_MAX_SIZE)
    add_payload("test3")

    key, value = span_mock.set_attribute.call_args[0]
    assert key == "test.attr"
    assert value.startswith("test1,test2test2")
    assert len(value) == PAYLOAD_MAX_SIZE
    assert "test3" not in value
