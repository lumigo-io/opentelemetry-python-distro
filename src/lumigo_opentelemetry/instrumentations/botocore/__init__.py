from lumigo_opentelemetry.instrumentations import AbstractInstrumentor
from lumigo_opentelemetry.instrumentations.botocore.parsers import AwsParser


class BotoCoreInstrumentorWrapper(AbstractInstrumentor):
    def __init__(self) -> None:
        super().__init__("botocore")

    def check_if_applicable(self) -> None:
        from botocore.client import BaseClient  # noqa
        from botocore.endpoint import Endpoint  # noqa
        from botocore.exceptions import ClientError  # noqa

    def install_instrumentation(self) -> None:
        from opentelemetry.instrumentation.botocore import BotocoreInstrumentor

        BotocoreInstrumentor().instrument(
            request_hook=AwsParser.request_hook,
            response_hook=AwsParser.response_hook,
        )


instrumentor: AbstractInstrumentor = BotoCoreInstrumentorWrapper()
