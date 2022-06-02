from lumigo_opentelemetry.instrumentations import AbstractInstrumentor


class KafkaInstrumentorWrapper(AbstractInstrumentor):
    def __init__(self):
        super().__init__("kafka")

    def check_if_applicable(self):
        import kafka  # noqa

    def install_instrumentation(self):
        from opentelemetry.instrumentation.kafka import KafkaInstrumentor

        KafkaInstrumentor().instrument()


instrumentor: AbstractInstrumentor = KafkaInstrumentorWrapper()
