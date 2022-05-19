try:
    import pymongo  # noqa
    from opentelemetry.instrumentation.pymongo import PymongoInstrumentor

    PymongoInstrumentor().instrument()
except ImportError:
    pass
