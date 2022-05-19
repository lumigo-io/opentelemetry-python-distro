try:
    import urllib  # noqa
    from opentelemetry.instrumentation.urllib import URLLibInstrumentor

    URLLibInstrumentor().instrument()
except ImportError:
    pass
