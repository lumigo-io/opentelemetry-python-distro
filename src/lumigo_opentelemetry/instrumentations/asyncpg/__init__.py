from lumigo_opentelemetry.instrumentations import AbstractInstrumentor


class AsyncPGInstrumentorWrapper(AbstractInstrumentor):
    def __init__(self):
        super().__init__("asyncpg")

    def check_if_applicable(self):
        import asyncpg  # noqa

    def install_instrumentation(self):
        from opentelemetry.instrumentation.aiopg import AsyncPGInstrumentor

        AsyncPGInstrumentor().instrument()


instrumentor: AbstractInstrumentor = AsyncPGInstrumentorWrapper()
