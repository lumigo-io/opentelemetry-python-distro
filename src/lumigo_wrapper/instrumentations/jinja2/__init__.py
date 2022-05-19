try:
    import jinja2  # noqa
    from opentelemetry.instrumentation.jinja2 import Jinja2Instrumentor

    Jinja2Instrumentor().instrument()
except ImportError:
    pass
