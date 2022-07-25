from lumigo_opentelemetry.instrumentations import AbstractInstrumentor

class SklearnInstrumentor(AbstractInstrumentor):
    def __init__(self) -> None:
        super().__init__("sklearn")

    def get_otel_instrumentor(self):
        from opentelemetry.instrumentation.sklearn import (
            SklearnInstrumentor as UpstreamInstrumentor,
        )

        return UpstreamInstrumentor()
