from lumigo_opentelemetry.instrumentations import AbstractInstrumentor


class RedisInstrumentor(AbstractInstrumentor):
    def __init__(self):
        super().__init__("redis")

    def check_if_applicable(self):
        import redis  # noqa

    def install_instrumentation(self):
        from opentelemetry.instrumentation.redis import RedisInstrumentor

        RedisInstrumentor().instrument()


instrumentor: AbstractInstrumentor = RedisInstrumentor()
