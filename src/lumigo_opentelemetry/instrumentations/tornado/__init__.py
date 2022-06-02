from lumigo_opentelemetry.instrumentations import AbstractInstrumentor


class TornadoInstrumentor(AbstractInstrumentor):
    def __init__(self):
        super().__init__("tornado")

    def check_if_applicable(self):
        import tornado.web  # noqa

    def install_instrumentation(self):
        from opentelemetry.instrumentation.tornado import TornadoInstrumentor

        TornadoInstrumentor().instrument()


instrumentor: AbstractInstrumentor = TornadoInstrumentor()
