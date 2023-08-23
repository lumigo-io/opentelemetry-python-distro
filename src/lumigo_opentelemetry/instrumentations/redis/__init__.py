import json
from typing import List, Any, Dict

from opentelemetry.trace.span import Span
from lumigo_opentelemetry.instrumentations import AbstractInstrumentor
from lumigo_opentelemetry.instrumentations.instrumentation_utils import (
    add_body_attribute,
)


class RedisInstrumentor(AbstractInstrumentor):
    def __init__(self) -> None:
        super().__init__("redis")

    def check_if_applicable(self) -> None:
        import redis  # noqa

    def install_instrumentation(self) -> None:
        from opentelemetry.instrumentation.redis import RedisInstrumentor
        from redis.connection import Connection

        def request_hook(
            span: Span, instance: Connection, args: List[Any], kwargs: Dict[Any, Any]
        ) -> None:
            add_body_attribute(span, json.dumps(args), "redis.request.args")
            add_body_attribute(span, json.dumps(kwargs), "redis.request.kwargs")

        def response_hook(span: Span, instance: Connection, response: Any) -> None:
            add_body_attribute(span, response, "redis.response.body")

        RedisInstrumentor().instrument(
            request_hook=request_hook,
            response_hook=response_hook,
        )


instrumentor: AbstractInstrumentor = RedisInstrumentor()
