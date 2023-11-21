from lumigo_opentelemetry.instrumentations import AbstractInstrumentor
from lumigo_opentelemetry.instrumentations.shared.psycopg import (
    patch_psycopg_for_payload_capture,
)


class Psycopg2Instrumentor(AbstractInstrumentor):
    def __init__(self) -> None:
        super().__init__("psycopg2")

    def check_if_applicable(self) -> None:
        import psycopg2  # noqa

    def install_instrumentation(self) -> None:

        from opentelemetry.instrumentation import psycopg2

        patch_psycopg_for_payload_capture(package=psycopg2)

        # if we don't skip the dependency check, the instrumentor will fail
        # because it can't detect psycopg2-binary
        psycopg2.Psycopg2Instrumentor().instrument(skip_dep_check=True)


instrumentor: AbstractInstrumentor = Psycopg2Instrumentor()
