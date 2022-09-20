from lumigo_opentelemetry.instrumentations import AbstractInstrumentor


class Boto3SQSInstrumentorWrapper(AbstractInstrumentor):
    def __init__(self) -> None:
        super().__init__("boto3sqs")

    def check_if_applicable(self) -> None:
        import boto  # noqa

    def install_instrumentation(self) -> None:
        from opentelemetry.instrumentation.boto3sqs import Boto3SQSInstrumentor

        Boto3SQSInstrumentor().instrument()


instrumentor: AbstractInstrumentor = Boto3SQSInstrumentorWrapper()
