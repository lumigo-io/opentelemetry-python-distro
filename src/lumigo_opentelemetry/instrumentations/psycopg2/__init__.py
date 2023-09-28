from lumigo_opentelemetry.instrumentations import AbstractInstrumentor


class Psycopg2Instrumentor(AbstractInstrumentor):
    def __init__(self) -> None:
        super().__init__("psycopg2")

    def check_if_applicable(self) -> None:
        import psycopg2  # noqa

    def install_instrumentation(self) -> None:
        from opentelemetry.instrumentation.psycopg2 import Psycopg2Instrumentor

        # if we don't skip the dependency check, the instrumentor will fail
        # because it can't detect psycopg2-binary
        Psycopg2Instrumentor().instrument(skip_dep_check=True)


instrumentor: AbstractInstrumentor = Psycopg2Instrumentor()
