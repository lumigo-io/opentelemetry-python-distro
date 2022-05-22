from lumigo_opentelemetry.instrumentations import AbstractInstrumentor


class GrpcInstrumentorWrapper(AbstractInstrumentor):
    def __init__(self):
        super().__init__("grpc")

    def check_if_applicable(self):
        import grpc  # noqa

    def install_instrumentation(self):
        from opentelemetry.instrumentation.grpc import GrpcInstrumentorClient

        GrpcInstrumentorClient().instrument()


instrumentor: AbstractInstrumentor = GrpcInstrumentorWrapper()
