try:
    from opentelemetry.instrumentation.pymemcache import PymemcacheInstrumentor

    PymemcacheInstrumentor().instrument()
except ImportError:
    pass
