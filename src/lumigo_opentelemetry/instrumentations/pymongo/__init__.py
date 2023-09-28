from typing import Union

from opentelemetry.trace.span import Span

from lumigo_opentelemetry.instrumentations import AbstractInstrumentor
from lumigo_opentelemetry import logger
from lumigo_opentelemetry.libs.general_utils import lumigo_safe_execute
from lumigo_opentelemetry.libs.json_utils import dump_with_context


class PymongoInstrumentor(AbstractInstrumentor):
    def __init__(self) -> None:
        super().__init__("pymongo")

    def check_if_applicable(self) -> None:
        import pymongo  # noqa

    def install_instrumentation(self) -> None:
        from opentelemetry.instrumentation.pymongo import PymongoInstrumentor
        from pymongo.monitoring import (
            CommandStartedEvent,
            CommandSucceededEvent,
            CommandFailedEvent,
        )

        def request_hook(span: Span, event: CommandStartedEvent) -> None:
            with lumigo_safe_execute("pymongo_request_hook"):
                span.set_attribute("db.statement", event.command_name)
                if isinstance(event, CommandStartedEvent):
                    span.set_attribute(
                        "db.request.body",
                        dump_with_context("requestBody", event.command),
                    )
                else:
                    logger.warning(f"Got unexpected event type {type(event)}")

        def response_hook(
            span: Span, event: Union[CommandSucceededEvent, CommandFailedEvent]
        ) -> None:
            with lumigo_safe_execute("pymongo_response_hook"):
                if isinstance(event, CommandSucceededEvent):
                    span.set_attribute(
                        "db.response.body",
                        dump_with_context("responseBody", event.reply),
                    )
                elif isinstance(event, CommandFailedEvent):
                    span.set_attribute(
                        "db.response.body",
                        dump_with_context("responseBody", event.failure),
                    )
                else:
                    logger.warning(f"Got unexpected event type {type(event)}")

        PymongoInstrumentor().instrument(
            request_hook=request_hook, response_hook=response_hook
        )


instrumentor: AbstractInstrumentor = PymongoInstrumentor()
