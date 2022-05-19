try:
    import pika  # noqa
    from opentelemetry.instrumentation.pika import PikaInstrumentor

    PikaInstrumentor().instrument()
except ImportError:
    pass
