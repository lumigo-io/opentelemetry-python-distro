try:
    import asyncpg  # noqa
    from opentelemetry.instrumentation.asyncpg import AsyncPGInstrumentor

    AsyncPGInstrumentor().instrument()
except ImportError:
    pass
