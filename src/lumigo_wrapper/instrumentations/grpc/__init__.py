try:
    import grpc  # noqa
    from opentelemetry.instrumentation.grpc import GrpcInstrumentorClient

    GrpcInstrumentorClient().instrument()
except ImportError:
    pass
