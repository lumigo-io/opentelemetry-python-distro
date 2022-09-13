from lumigo_opentelemetry.instrumentations import AbstractInstrumentor


class RedisInstrumentor(AbstractInstrumentor):
    def __init__(self) -> None:
        super().__init__("redis")

    def check_if_applicable(self) -> None:
        import redis  # noqa

    def install_instrumentation(self) -> None:
        from opentelemetry.instrumentation.redis import RedisInstrumentor

        RedisInstrumentor().instrument()


instrumentor: AbstractInstrumentor = RedisInstrumentor()
