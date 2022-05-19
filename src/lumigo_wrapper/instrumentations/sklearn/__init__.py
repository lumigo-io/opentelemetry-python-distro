try:
    from opentelemetry.instrumentation.sklearn import SklearnInstrumentor

    SklearnInstrumentor().instrument()
except ImportError:
    pass
