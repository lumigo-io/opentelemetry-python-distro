try:
    import urllib3  # noqa
    from opentelemetry.instrumentation.urllib3 import URLLib3Instrumentor

    URLLib3Instrumentor().instrument()
except ImportError:
    pass
