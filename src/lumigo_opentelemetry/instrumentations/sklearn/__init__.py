from lumigo_opentelemetry.instrumentations import AbstractInstrumentor


class SklearnInstrumentor(AbstractInstrumentor):
    def __init__(self) -> None:
        super().__init__("sklearn")

    def check_if_applicable(self) -> None:
        from sklearn.base import BaseEstimator  # noqa
        from sklearn.pipeline import FeatureUnion, Pipeline  # noqa
        from sklearn.tree import BaseDecisionTree  # noqa
        from sklearn.utils.metaestimators import _IffHasAttrDescriptor  # noqa

    def install_instrumentation(self) -> None:
        from opentelemetry.instrumentation.sklearn import SklearnInstrumentor

        SklearnInstrumentor().instrument()


instrumentor: AbstractInstrumentor = SklearnInstrumentor()
