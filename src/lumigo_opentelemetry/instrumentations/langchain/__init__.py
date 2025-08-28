from lumigo_opentelemetry import logger

from lumigo_opentelemetry.instrumentations import AbstractInstrumentor


class LangchainInstrumentorWrapper(AbstractInstrumentor):
    def __init__(self) -> None:
        super().__init__("langchain")

    def is_disabled_on_lambda(self) -> bool:
        return False

    def assert_instrumented_package_importable(self) -> None:
        import langchain  # noqa

    def install_instrumentation(self) -> None:
        from opentelemetry.instrumentation.langchain import LangchainInstrumentor

        logger.info("Installing OpenLLMetry instrumentation for Langchain")
        LangchainInstrumentor().instrument()


instrumentor: AbstractInstrumentor = LangchainInstrumentorWrapper()
