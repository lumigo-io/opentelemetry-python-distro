try:
    import httpx  # noqa
    from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

    HTTPXClientInstrumentor().instrument()
except ImportError:
    pass
