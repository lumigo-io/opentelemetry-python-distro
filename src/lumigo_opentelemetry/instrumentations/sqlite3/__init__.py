from lumigo_opentelemetry.instrumentations import AbstractInstrumentor


class SQLite3Instrumentor(AbstractInstrumentor):
    def __init__(self):
        super().__init__("sqlite3")

    def check_if_applicable(self):
        import sqlite3  # noqa

    def install_instrumentation(self):
        from opentelemetry.instrumentation.sqlite3 import SQLite3Instrumentor

        SQLite3Instrumentor().instrument()


instrumentor: AbstractInstrumentor = SQLite3Instrumentor()
