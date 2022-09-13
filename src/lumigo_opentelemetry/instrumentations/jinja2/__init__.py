from lumigo_opentelemetry.instrumentations import AbstractInstrumentor


class Jinja2InstrumentorWrapper(AbstractInstrumentor):
    def __init__(self) -> None:
        super().__init__("jinja2")

    def check_if_applicable(self) -> None:
        import jinja2  # noqa

    def install_instrumentation(self) -> None:
        from opentelemetry.instrumentation.jinja2 import Jinja2Instrumentor

        Jinja2Instrumentor().instrument()


instrumentor: AbstractInstrumentor = Jinja2InstrumentorWrapper()
