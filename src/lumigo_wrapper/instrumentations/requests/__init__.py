try:
    from opentelemetry.instrumentation.requests import RequestsInstrumentor

    from lumigo_wrapper.instrumentations.requests.requests_instrumentation import (
        HttpParser,
    )

    RequestsInstrumentor().instrument(span_callback=HttpParser.request_callback)
except ImportError:
    pass
