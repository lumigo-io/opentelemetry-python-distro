from typing import Any, Dict, List, Optional
from lumigo_opentelemetry.instrumentations import AbstractInstrumentor
from opentelemetry.instrumentation.instrumentor import BaseInstrumentor
from .parsers import FastAPIParser


class FastApiInstrumentor(AbstractInstrumentor):
    def __init__(self) -> None:
        super().__init__("fastapi")

    def get_otel_instrumentor(self) -> BaseInstrumentor:
        from opentelemetry.instrumentation.fastapi import (
            FastAPIInstrumentor as UpstreamInstrumentor,
        )

        return UpstreamInstrumentor()

    def _do_instrument(self, instrumentor: BaseInstrumentor) -> None:
        import wrapt
        from lumigo_opentelemetry import logger

        @wrapt.patch_function_wrapper("fastapi", "FastAPI.__init__")
        def init_otel_middleware(wrapped, instance: Any, args: Optional[List[Any]], kwargs: Optional[Dict[str, Any]]):  # type: ignore
            try:
                return_value = wrapped(*args, **kwargs)
                instrumentor.instrument_app(
                    instance,
                    server_request_hook=FastAPIParser.server_request_hook,
                    client_request_hook=FastAPIParser.client_request_hook,
                    client_response_hook=FastAPIParser.client_response_hook,
                )

                return return_value

            except Exception as e:
                logger.exception("failed instrumenting FastAPI", exc_info=e)
