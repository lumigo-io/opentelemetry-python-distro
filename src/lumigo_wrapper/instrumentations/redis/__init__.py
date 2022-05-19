try:
    import redis  # noqa
    from opentelemetry.instrumentation.redis import RedisInstrumentor

    RedisInstrumentor().instrument()
except ImportError:
    pass
