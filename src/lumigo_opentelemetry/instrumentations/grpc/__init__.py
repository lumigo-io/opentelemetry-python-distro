from lumigo_opentelemetry.instrumentations import AbstractInstrumentor
from opentelemetry.instrumentation.instrumentor import BaseInstrumentor


class GrpcInstrumentor(AbstractInstrumentor):
    def __init__(self) -> None:
        super().__init__("grpc")

    def get_otel_instrumentor(self) -> BaseInstrumentor:
        from opentelemetry.instrumentation.grpc import (
            GrpcInstrumentorClient as UpstreamInstrumentor,
        )

        return UpstreamInstrumentor()
