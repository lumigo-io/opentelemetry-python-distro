from lumigo_opentelemetry.instrumentations import AbstractInstrumentor
from lumigo_opentelemetry.instrumentations.botocore.parsers import AwsParser

class BotoCoreInstrumentor(AbstractInstrumentor):
    def __init__(self):
        super().__init__("botocore")

    def get_otel_instrumentor(self):
        from opentelemetry.instrumentation.botocore import (
            BotocoreInstrumentor as UpstreamInstrumentor,
        )

        return UpstreamInstrumentor()

    def _do_instrument(self, instrumentor):
        instrumentor.instrument(
            request_hook=AwsParser.request_hook,
            response_hook=AwsParser.response_hook,
        )
