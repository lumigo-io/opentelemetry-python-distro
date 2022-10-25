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
        # We're using a copied version of this instrumentor until this PR will be merged:
        # https://github.com/open-telemetry/opentelemetry-python-contrib/pull/1350
        # After the merge, delete the following line and uncomment the next line
        from lumigo_opentelemetry.external.botocore import BotocoreInstrumentor

        # from opentelemetry.instrumentation.botocore import BotocoreInstrumentor

        BotocoreInstrumentor().instrument(
            request_hook=AwsParser.request_hook,
            response_hook=AwsParser.response_hook,
        )


instrumentor: AbstractInstrumentor = BotoCoreInstrumentorWrapper()
