from lumigo_opentelemetry.instrumentations import AbstractInstrumentor


class GrpcInstrumentorWrapper(AbstractInstrumentor):
    def __init__(self) -> None:
        super().__init__("grpc")

    def check_if_applicable(self) -> None:
        import grpc  # noqa

    def install_instrumentation(self) -> None:
        from opentelemetry.instrumentation.grpc import GrpcInstrumentorClient

        GrpcInstrumentorClient().instrument()


instrumentor: AbstractInstrumentor = GrpcInstrumentorWrapper()
