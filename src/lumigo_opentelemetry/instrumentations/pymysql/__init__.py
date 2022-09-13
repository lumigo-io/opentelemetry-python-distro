from lumigo_opentelemetry.instrumentations import AbstractInstrumentor


class PyMySqlInstrumentor(AbstractInstrumentor):
    def __init__(self) -> None:
        super().__init__("pymysql")

    def check_if_applicable(self) -> None:
        import pymysql  # noqa

    def install_instrumentation(self) -> None:
        from opentelemetry.instrumentation.pymysql import PyMySQLInstrumentor

        PyMySQLInstrumentor().instrument()


instrumentor: AbstractInstrumentor = PyMySqlInstrumentor()
