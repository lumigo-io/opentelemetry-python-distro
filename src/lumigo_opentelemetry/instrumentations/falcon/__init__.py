from lumigo_opentelemetry.instrumentations import AbstractInstrumentor


class FalconInstrumentorWrapper(AbstractInstrumentor):
    def __init__(self) -> None:
        super().__init__("falcon")

    def check_if_applicable(self) -> None:
        import falcon  # noqa

    def install_instrumentation(self) -> None:
        from opentelemetry.instrumentation.falcon import FalconInstrumentor

        FalconInstrumentor().instrument()


instrumentor: AbstractInstrumentor = FalconInstrumentorWrapper()
