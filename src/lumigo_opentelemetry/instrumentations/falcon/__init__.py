from lumigo_opentelemetry.instrumentations import AbstractInstrumentor


class FalconInstrumentorWrapper(AbstractInstrumentor):
    def __init__(self):
        super().__init__("falcon")

    def check_if_applicable(self):
        import falcon  # noqa

    def install_instrumentation(self):
        from opentelemetry.instrumentation.falcon import FalconInstrumentor

        FalconInstrumentor().instrument()


instrumentor: AbstractInstrumentor = FalconInstrumentorWrapper()
