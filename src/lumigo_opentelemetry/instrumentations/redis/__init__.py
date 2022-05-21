from .. import AbstractInstrumentor

class RedisInstrumentor(AbstractInstrumentor):

    def __init__(self):
        super().__init__("redis")

    def check_if_applicable(self):
        import redis  # noqa

    def install_instrumentation(self):
        from opentelemetry.instrumentation.pymysql import PyMySQLInstrumentor

        RedisInstrumentor().instrument()

instrumentor = RedisInstrumentor()
