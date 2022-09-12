from lumigo_opentelemetry.instrumentations import AbstractInstrumentor


class PymemcacheInstrumentor(AbstractInstrumentor):
    def __init__(self) -> None:
        super().__init__("pymemcache")

    def check_if_applicable(self) -> None:
        import pymemcache  # noqa

    def install_instrumentation(self) -> None:
        from opentelemetry.instrumentation.pymemcache import PymemcacheInstrumentor

        PymemcacheInstrumentor().instrument()


instrumentor: AbstractInstrumentor = PymemcacheInstrumentor()
