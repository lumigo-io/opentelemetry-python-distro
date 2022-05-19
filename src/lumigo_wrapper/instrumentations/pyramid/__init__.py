try:
    import pyramid.config  # noqa
    from opentelemetry.instrumentation.pyramid import PyramidInstrumentor

    PyramidInstrumentor().instrument()
except ImportError:
    pass
