try:
    import mysql.connector  # noqa
    from opentelemetry.instrumentation.mysql import MySQLInstrumentor

    MySQLInstrumentor().instrument()
except ImportError:
    pass
