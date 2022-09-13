from lumigo_opentelemetry.instrumentations import AbstractInstrumentor


class AioPgInstrumentorWrapper(AbstractInstrumentor):
    def __init__(self) -> None:
        super().__init__("aiopg")

    def check_if_applicable(self) -> None:
        import aiopg  # noqa

    def install_instrumentation(self) -> None:
        from opentelemetry.instrumentation.aiopg import AiopgInstrumentor

        AiopgInstrumentor().instrument()


instrumentor: AbstractInstrumentor = AioPgInstrumentorWrapper()
