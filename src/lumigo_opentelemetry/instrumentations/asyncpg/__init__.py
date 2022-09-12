from lumigo_opentelemetry.instrumentations import AbstractInstrumentor


class AsyncPGInstrumentorWrapper(AbstractInstrumentor):
    def __init__(self) -> None:
        super().__init__("asyncpg")

    def check_if_applicable(self) -> None:
        import asyncpg  # noqa

    def install_instrumentation(self) -> None:
        from opentelemetry.instrumentation.aiopg import AsyncPGInstrumentor

        AsyncPGInstrumentor().instrument()


instrumentor: AbstractInstrumentor = AsyncPGInstrumentorWrapper()
