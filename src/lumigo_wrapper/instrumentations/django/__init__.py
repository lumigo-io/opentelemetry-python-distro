try:
    import django  # noqa

    from opentelemetry.instrumentation.django import DjangoInstrumentor
    from lumigo_wrapper.instrumentations.instrumentations import frameworks, Framework

    DjangoInstrumentor().instrument()
    frameworks.append(Framework.Django)
except ImportError:
    pass
