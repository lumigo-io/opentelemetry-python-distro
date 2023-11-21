from lumigo_opentelemetry.instrumentations import AbstractInstrumentor
from lumigo_opentelemetry.instrumentations.shared.psycopg import (
    patch_psycopg_for_payload_capture,
)


class PsycopgInstrumentor(AbstractInstrumentor):
    def __init__(self) -> None:
        super().__init__("psycopg")

    def check_if_applicable(self) -> None:
        import psycopg  # noqa

    def install_instrumentation(self) -> None:

        from . import instrumentation as psycopg

        patch_psycopg_for_payload_capture(package=psycopg)

        # if we don't skip the dependency check, the instrumentor will fail
        # because it can't detect psycopg2-binary
        psycopg.PsycopgInstrumentor().instrument(skip_dep_check=True)


instrumentor: AbstractInstrumentor = PsycopgInstrumentor()
