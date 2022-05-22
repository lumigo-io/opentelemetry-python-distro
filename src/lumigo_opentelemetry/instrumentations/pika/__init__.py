from lumigo_opentelemetry.instrumentations import AbstractInstrumentor


class PikaInstrumentorWrapper(AbstractInstrumentor):
    def __init__(self):
        super().__init__("pika")

    def check_if_applicable(self):
        import pika  # noqa

    def install_instrumentation(self):
        from opentelemetry.instrumentation.pika import PikaInstrumentor

        PikaInstrumentor().instrument()


instrumentor: AbstractInstrumentor = PikaInstrumentorWrapper()
