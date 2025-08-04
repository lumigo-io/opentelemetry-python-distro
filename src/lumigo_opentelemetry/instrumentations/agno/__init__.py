from lumigo_opentelemetry import logger

from lumigo_opentelemetry.instrumentations import AbstractInstrumentor


class AgnoInstrumentorWrapper(AbstractInstrumentor):
    def __init__(self) -> None:
        super().__init__("agno")

    def is_disabled_on_lambda(self) -> bool:
        return False

    def assert_instrumented_package_importable(self) -> None:
        import agno  # noqa

    def install_instrumentation(self) -> None:
        from openinference.instrumentation.agno import AgnoInstrumentor

        logger.info("Installing OpenInference instrumentation for Agno")
        AgnoInstrumentor().instrument()


instrumentor: AbstractInstrumentor = AgnoInstrumentorWrapper()
