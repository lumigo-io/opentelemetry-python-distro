from lumigo_opentelemetry.instrumentations import AbstractInstrumentor


class BotoInstrumentorWrapper(AbstractInstrumentor):
    def __init__(self):
        super().__init__("boto")

    def check_if_applicable(self):
        from botocore.client import BaseClient  # noqa
        from botocore.endpoint import Endpoint  # noqa
        from botocore.exceptions import ClientError  # noqa

    def install_instrumentation(self):
        from opentelemetry.instrumentation.boto import BotoInstrumentor
        from opentelemetry.instrumentation.botocore import BotocoreInstrumentor

        from . import (
            AwsParser,
        )

        BotocoreInstrumentor().instrument(
            request_hook=AwsParser.request_hook,
            response_hook=AwsParser.response_hook,
        )
        BotoInstrumentor().instrument()


instrumentor: AbstractInstrumentor = BotoInstrumentorWrapper()
