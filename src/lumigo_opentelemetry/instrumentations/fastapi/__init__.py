from lumigo_opentelemetry.instrumentations import AbstractInstrumentor
from .parsers import FastAPIParser


class FastApiInstrumentorWrapper(AbstractInstrumentor):
    def __init__(self) -> None:
        super().__init__("fast-api")

    def check_if_applicable(self) -> None:
        import fastapi  # noqa

    def install_instrumentation(self) -> None:
        import wrapt

        from lumigo_opentelemetry import logger

        @wrapt.patch_function_wrapper("fastapi", "FastAPI.__init__")
        def init_otel_middleware(wrapped, instance, args, kwargs):  # type: ignore
            try:
                from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

                return_value = wrapped(*args, **kwargs)
                FastAPIInstrumentor().instrument_app(
                    instance,
                    server_request_hook=FastAPIParser.server_request_hook,
                    client_request_hook=FastAPIParser.client_request_hook,
                    client_response_hook=FastAPIParser.client_response_hook,
                )

                return return_value

            except Exception as e:
                logger.exception("failed instrumenting FastAPI", exc_info=e)


instrumentor: AbstractInstrumentor = FastApiInstrumentorWrapper()
