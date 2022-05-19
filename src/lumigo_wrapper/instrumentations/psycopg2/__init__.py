try:
    import psycopg2  # noqa
    from opentelemetry.instrumentation.psycopg2 import Psycopg2Instrumentor

    Psycopg2Instrumentor().instrument()
except ImportError:
    pass
