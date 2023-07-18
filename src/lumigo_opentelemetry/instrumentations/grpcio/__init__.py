from lumigo_opentelemetry.instrumentations import AbstractInstrumentor
from .common import SHOULD_INSTRUMENT_PAYLOADS


class GRPCInstrumentor(AbstractInstrumentor):
    def __init__(self) -> None:
        super().__init__("grpc")

    def check_if_applicable(self) -> None:
        import grpc  # noqa

    @staticmethod
    def inject_lumigo_interceptors() -> None:
        from .grpc_instrument_client import LumigoClientInterceptor
        from .grpc_instrument_server import LumigoServerInterceptor
        from opentelemetry.instrumentation.grpc import _client, _server

        _client.OpenTelemetryClientInterceptor = LumigoClientInterceptor
        _server.OpenTelemetryServerInterceptor = LumigoServerInterceptor

    def install_instrumentation(self) -> None:
        from opentelemetry.instrumentation.grpc import (
            GrpcInstrumentorServer,
            GrpcInstrumentorClient,
        )

        if SHOULD_INSTRUMENT_PAYLOADS:
            self.inject_lumigo_interceptors()
        GrpcInstrumentorServer().instrument()
        GrpcInstrumentorClient().instrument()


instrumentor: AbstractInstrumentor = GRPCInstrumentor()
