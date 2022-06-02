from lumigo_opentelemetry.instrumentations import AbstractInstrumentor


class PyramidInstrumentor(AbstractInstrumentor):
    def __init__(self):
        super().__init__("pyramid")

    def check_if_applicable(self):
        import pyramid.config  # noqa

    def install_instrumentation(self):
        from opentelemetry.instrumentation.pyramid import PyramidInstrumentor

        PyramidInstrumentor().instrument()


instrumentor: AbstractInstrumentor = PyramidInstrumentor()
