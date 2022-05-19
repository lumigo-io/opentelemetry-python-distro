try:
    import sqlite3  # noqa
    from opentelemetry.instrumentation.sqlite3 import SQLite3Instrumentor

    SQLite3Instrumentor().instrument()
except ImportError:
    pass
