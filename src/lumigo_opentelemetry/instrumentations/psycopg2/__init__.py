from lumigo_opentelemetry.instrumentations import AbstractInstrumentor


class Psycopg2InstrumentorWrapper(AbstractInstrumentor):
    def __init__(self):
        super().__init__("psycopg2")

    def check_if_applicable(self):
        import psycopg2  # noqa

    def install_instrumentation(self):
        from opentelemetry.instrumentation.psycopg2 import Psycopg2Instrumentor

        Psycopg2Instrumentor().instrument()


instrumentor: AbstractInstrumentor = Psycopg2InstrumentorWrapper()
