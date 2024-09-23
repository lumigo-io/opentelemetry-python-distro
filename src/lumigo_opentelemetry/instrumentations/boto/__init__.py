from lumigo_opentelemetry.instrumentations import AbstractInstrumentor


class BotoInstrumentorWrapper(AbstractInstrumentor):
    def __init__(self) -> None:
        super().__init__("boto")

    def assert_instrumented_package_importable(self) -> None:
        import boto  # noqa

    def install_instrumentation(self) -> None:
        from opentelemetry.instrumentation.boto import BotoInstrumentor

        BotoInstrumentor().instrument()


instrumentor: AbstractInstrumentor = BotoInstrumentorWrapper()
