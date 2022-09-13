from lumigo_opentelemetry.instrumentations import AbstractInstrumentor


class SQLite3Instrumentor(AbstractInstrumentor):
    def __init__(self) -> None:
        super().__init__("sqlite3")

    def check_if_applicable(self) -> None:
        import sqlite3  # noqa

    def install_instrumentation(self) -> None:
        from opentelemetry.instrumentation.sqlite3 import SQLite3Instrumentor

        SQLite3Instrumentor().instrument()


instrumentor: AbstractInstrumentor = SQLite3Instrumentor()
