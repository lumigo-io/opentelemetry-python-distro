from typing import Any, Dict

from opentelemetry.trace.span import Span
from lumigo_opentelemetry import logger

from lumigo_opentelemetry.instrumentations import AbstractInstrumentor


class OpenLLMetryInstrumentorWrapper(AbstractInstrumentor):
    def __init__(self) -> None:
        super().__init__("openllmetry")

    def assert_instrumented_package_importable(self) -> None:
        import langgraph  # noqa

    def install_instrumentation(self) -> None:
        from opentelemetry.instrumentation.langchain import LangchainInstrumentor

        logger.info("Installing OpenLLMetry instrumentation for Langchain")
        LangchainInstrumentor().instrument()


instrumentor: AbstractInstrumentor = OpenLLMetryInstrumentorWrapper()
