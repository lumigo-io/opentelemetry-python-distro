from lumigo_opentelemetry.instrumentations import AbstractInstrumentor


class KafkaPythonInstrumentor(AbstractInstrumentor):
    def __init__(self) -> None:
        super().__init__("kafka_python")

    def check_if_applicable(self) -> None:
        import kafka  # noqa

    def install_instrumentation(self) -> None:
        from opentelemetry.instrumentation.kafka import KafkaInstrumentor

        KafkaInstrumentor().instrument()


instrumentor: AbstractInstrumentor = KafkaPythonInstrumentor()
