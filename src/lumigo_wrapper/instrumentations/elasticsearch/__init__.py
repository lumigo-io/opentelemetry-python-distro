try:
    import elasticsearch  # noqa
    from opentelemetry.instrumentation.elasticsearch import ElasticsearchInstrumentor

    ElasticsearchInstrumentor().instrument()
except ImportError:
    pass
