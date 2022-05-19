try:
    import aiopg  # noqa
    from opentelemetry.instrumentation.aiopg import AiopgInstrumentor

    AiopgInstrumentor().instrument()
except ImportError:
    pass
