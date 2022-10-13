from lumigo_opentelemetry.instrumentations import AbstractInstrumentor
from lumigo_opentelemetry.instrumentations.botocore.parsers import AwsParser
from opentelemetry.instrumentation.instrumentor import BaseInstrumentor


class BotoCoreInstrumentor(AbstractInstrumentor):
    def __init__(self) -> None:
        super().__init__("botocore")

    def get_otel_instrumentor(self) -> BaseInstrumentor:
        from opentelemetry.instrumentation.botocore import (
            BotocoreInstrumentor as UpstreamInstrumentor,
        )

        return UpstreamInstrumentor()

    def _do_instrument(self, instrumentor: BaseInstrumentor) -> None:
        instrumentor.instrument(
            request_hook=AwsParser.request_hook,
            response_hook=AwsParser.response_hook,
        )
