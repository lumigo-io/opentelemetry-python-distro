from abc import abstractmethod, ABC


class AbstractInstrumentor(ABC):
    """This class wraps around the facilities of opentelemetry.instrumentation.BaseInstrumentor
    to provide a safer baseline in terms of dependency checks than what is available upstream.
    """

    # TODO Implement lookup of package versions based on the file-based version ranges we validate

    @abstractmethod
    def __init__(self, instrumentation_id: str):
        self._instrumentation_id = instrumentation_id

    @abstractmethod
    def check_if_applicable(self) -> None:
        # TODO Implement version lookup per instrumented package, and check that the version is supported
        raise Exception("'check_if_applicable' method not implemented!")

    @abstractmethod
    def install_instrumentation(self) -> None:
        raise Exception("'apply_instrumentation' method not implemented!")

    @property
    def instrumentation_id(self) -> str:
        return self._instrumentation_id
