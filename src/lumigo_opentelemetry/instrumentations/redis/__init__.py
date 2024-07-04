from typing import Any, Dict, List

from opentelemetry.trace.span import Span

from lumigo_opentelemetry.instrumentations import AbstractInstrumentor
from lumigo_opentelemetry.instrumentations.instrumentation_utils import (
    add_body_attribute,
)
from lumigo_opentelemetry.libs.general_utils import lumigo_safe_execute


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
            with lumigo_safe_execute("redis_request_hook"):
                # a db.statement attribute is automatically added by the RedisInstrumentor
                # when this hook is called, but only includes the command name for some
                # versions so we need to set it ourselves.
                add_body_attribute(
                    span, " ".join(str(arg) for arg in args), "db.statement"
                )

        def response_hook(span: Span, instance: Connection, response: Any) -> None:
            with lumigo_safe_execute("redis_response_hook"):
                add_body_attribute(span, response, "db.response.body")

        RedisInstrumentor().instrument(
            request_hook=request_hook,
            response_hook=response_hook,
        )


instrumentor: AbstractInstrumentor = RedisInstrumentor()
