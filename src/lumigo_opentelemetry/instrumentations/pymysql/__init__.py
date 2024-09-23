from lumigo_opentelemetry.instrumentations import AbstractInstrumentor


class PyMySqlInstrumentor(AbstractInstrumentor):
    def __init__(self) -> None:
        super().__init__("pymysql")

    def assert_instrumented_package_importable(self) -> None:
        import pymysql  # noqa

    def install_instrumentation(self) -> None:
        from opentelemetry.instrumentation.pymysql import PyMySQLInstrumentor

        PyMySQLInstrumentor().instrument()


instrumentor: AbstractInstrumentor = PyMySqlInstrumentor()
