from lumigo_opentelemetry.instrumentations import AbstractInstrumentor


class GRPCInstrumentor(AbstractInstrumentor):
    def __init__(self) -> None:
        super().__init__("grpc")

    def check_if_applicable(self) -> None:
        import grpc  # noqa

    def install_instrumentation(self) -> None:
        from opentelemetry.instrumentation.grpc import (
            GrpcInstrumentorServer,
            GrpcInstrumentorClient,
        )

        GrpcInstrumentorServer().instrument()
        GrpcInstrumentorClient().instrument()


instrumentor: AbstractInstrumentor = GRPCInstrumentor()
