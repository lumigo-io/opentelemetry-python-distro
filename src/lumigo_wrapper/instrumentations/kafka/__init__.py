try:
    import kafka  # noqa
    from opentelemetry.instrumentation.kafka import KafkaInstrumentor

    KafkaInstrumentor().instrument()
except ImportError:
    pass
