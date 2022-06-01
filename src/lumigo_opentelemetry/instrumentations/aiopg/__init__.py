from lumigo_opentelemetry.instrumentations import AbstractInstrumentor


class AioPgInstrumentorWrapper(AbstractInstrumentor):
    def __init__(self):
        super().__init__("aiopg")

    def check_if_applicable(self):
        import aiopg  # noqa

    def install_instrumentation(self):
        from opentelemetry.instrumentation.aiopg import AiopgInstrumentor

        AiopgInstrumentor().instrument()


instrumentor: AbstractInstrumentor = AioPgInstrumentorWrapper()
