from lumigo_opentelemetry.instrumentations import AbstractInstrumentor


class PyMySqlInstrumentor(AbstractInstrumentor):
    def __init__(self):
        super().__init__("pymysql")

    def check_if_applicable(self):
        import pymysql  # noqa

    def install_instrumentation(self):
        from opentelemetry.instrumentation.pymysql import PyMySQLInstrumentor

        PyMySQLInstrumentor().instrument()


instrumentor: AbstractInstrumentor = PyMySqlInstrumentor()
