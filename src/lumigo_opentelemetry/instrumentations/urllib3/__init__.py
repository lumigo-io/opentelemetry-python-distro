from lumigo_opentelemetry.instrumentations import AbstractInstrumentor

class URLLib3Instrumentor(AbstractInstrumentor):
    def __init__(self) -> None:
        super().__init__("urllib3")

    def get_otel_instrumentor(self):
        from opentelemetry.instrumentation.urllib3 import (
            URLLib3Instrumentor as UpstreamInstrumentor,
        )

        return UpstreamInstrumentor()
