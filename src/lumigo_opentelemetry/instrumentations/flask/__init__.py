from typing import Any, Dict, List, Optional
from lumigo_opentelemetry.instrumentations import AbstractInstrumentor
from opentelemetry.instrumentation.instrumentor import BaseInstrumentor


class FlaskInstrumentor(AbstractInstrumentor):
    def __init__(self) -> None:
        super().__init__("flask")

    def get_otel_instrumentor(self) -> BaseInstrumentor:
        from opentelemetry.instrumentation.flask import (
            FlaskInstrumentor as UpstreamInstrumentor,
        )

        return UpstreamInstrumentor()

    def _do_instrument(self, instrumentor: BaseInstrumentor) -> None:
        import wrapt
        from lumigo_opentelemetry import logger

        @wrapt.patch_function_wrapper("flask", "Flask.__init__")
        def init_otel_flask_instrumentation(wrapped: Any, instance: Any, args: Optional[List[Any]], kwargs: Optional[Dict[str, Any]]):  # type: ignore
            try:
                return_value = wrapped(*args, **kwargs)
                instrumentor.instrument_app(instance)
                return return_value
            except Exception as e:
                logger.exception("failed instrumenting Flask", exc_info=e)
