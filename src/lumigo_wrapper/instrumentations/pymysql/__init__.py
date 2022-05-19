try:
    import pymysql  # noqa
    from opentelemetry.instrumentation.pymysql import PyMySQLInstrumentor

    PyMySQLInstrumentor().instrument()
except ImportError:
    pass
