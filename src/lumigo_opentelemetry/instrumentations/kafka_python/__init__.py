from typing import Dict, List, Any

from opentelemetry.trace.span import Span

from lumigo_opentelemetry.instrumentations import AbstractInstrumentor
from lumigo_opentelemetry.instrumentations.instrumentation_utils import (
    add_body_attribute,
)
from lumigo_opentelemetry.libs.general_utils import lumigo_safe_execute


class KafkaPythonInstrumentor(AbstractInstrumentor):
    def __init__(self) -> None:
        super().__init__("kafka_python")

    def check_if_applicable(self) -> None:
        import kafka  # noqa

    def install_instrumentation(self) -> None:
        from opentelemetry.instrumentation.kafka import KafkaInstrumentor
        from kafka.record.abc import ABCRecord

        def _produce_hook(span: Span, args: List[Any], kwargs: Dict[Any, Any]) -> None:
            with lumigo_safe_execute("kafka _produce_hook"):
                value = kwargs.get("value")
                if value is None and len(args) > 1:
                    value = args[1]
                add_body_attribute(span, value, "messaging.produce.body")

        def _consume_hook(
            span: Span, record: ABCRecord, args: List[Any], kwargs: Dict[Any, Any]
        ) -> None:
            with lumigo_safe_execute("kafka _consume_hook"):
                add_body_attribute(span, record.value, "messaging.consume.body")

        KafkaInstrumentor().instrument(
            produce_hook=_produce_hook, consume_hook=_consume_hook
        )


instrumentor: AbstractInstrumentor = KafkaPythonInstrumentor()
