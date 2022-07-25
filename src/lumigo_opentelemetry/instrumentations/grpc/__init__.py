from lumigo_opentelemetry.instrumentations import AbstractInstrumentor

class GrpcInstrumentor(AbstractInstrumentor):
    def __init__(self):
        super().__init__("grpc")

    def get_otel_instrumentor(self):
        from opentelemetry.instrumentation.grpc import (
            GrpcInstrumentorClient as UpstreamInstrumentor,
        )

        return UpstreamInstrumentor()
