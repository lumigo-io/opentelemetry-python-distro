from lumigo_opentelemetry.instrumentations import AbstractInstrumentor


class MySqlInstrumentorWrapper(AbstractInstrumentor):
    def __init__(self):
        super().__init__("mysql")

    def check_if_applicable(self):
        import mysql.connector  # noqa

    def install_instrumentation(self):
        from opentelemetry.instrumentation.mysql import MySQLInstrumentor

        MySQLInstrumentor().instrument()


instrumentor: AbstractInstrumentor = MySqlInstrumentorWrapper()
