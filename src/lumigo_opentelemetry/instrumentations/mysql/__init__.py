from lumigo_opentelemetry.instrumentations import AbstractInstrumentor


class MySqlInstrumentorWrapper(AbstractInstrumentor):
    def __init__(self) -> None:
        super().__init__("mysql")

    def check_if_applicable(self) -> None:
        import mysql.connector  # noqa

    def install_instrumentation(self) -> None:
        from opentelemetry.instrumentation.mysql import MySQLInstrumentor

        MySQLInstrumentor().instrument()


instrumentor: AbstractInstrumentor = MySqlInstrumentorWrapper()
