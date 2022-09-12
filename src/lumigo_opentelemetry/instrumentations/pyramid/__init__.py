from lumigo_opentelemetry.instrumentations import AbstractInstrumentor


class PyramidInstrumentor(AbstractInstrumentor):
    def __init__(self) -> None:
        super().__init__("pyramid")

    def check_if_applicable(self) -> None:
        import pyramid.config  # noqa

    def install_instrumentation(self) -> None:
        from opentelemetry.instrumentation.pyramid import PyramidInstrumentor

        PyramidInstrumentor().instrument()


instrumentor: AbstractInstrumentor = PyramidInstrumentor()
