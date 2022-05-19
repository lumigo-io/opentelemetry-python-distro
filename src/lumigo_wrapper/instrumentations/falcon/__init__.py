try:
    import falcon  # noqa
    from opentelemetry.instrumentation.falcon import FalconInstrumentor

    FalconInstrumentor().instrument()
except ImportError:
    pass
