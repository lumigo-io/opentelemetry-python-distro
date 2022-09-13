from lumigo_opentelemetry.instrumentations import AbstractInstrumentor


class AioHttpInstrumentorWrapper(AbstractInstrumentor):
    def __init__(self) -> None:
        super().__init__("aiohttp_client")

    def check_if_applicable(self) -> None:
        import aiohttp  # noqa

    def install_instrumentation(self) -> None:
        from opentelemetry.instrumentation.aiohttp_client import (
            AioHttpClientInstrumentor,
        )

        AioHttpClientInstrumentor().instrument()


instrumentor: AbstractInstrumentor = AioHttpInstrumentorWrapper()
