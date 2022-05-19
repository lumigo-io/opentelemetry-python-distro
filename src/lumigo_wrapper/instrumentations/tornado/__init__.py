try:
    import tornado.web  # noqa
    from opentelemetry.instrumentation.tornado import TornadoInstrumentor

    TornadoInstrumentor().instrument()
except ImportError:
    pass
