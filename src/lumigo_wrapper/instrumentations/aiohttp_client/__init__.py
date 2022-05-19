try:
    import aiohttp  # noqa
    from opentelemetry.instrumentation.aiohttp_client import AioHttpClientInstrumentor

    AioHttpClientInstrumentor().instrument()
except ImportError:
    pass
