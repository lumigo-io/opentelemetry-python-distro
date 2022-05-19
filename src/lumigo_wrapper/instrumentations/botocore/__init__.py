try:
    from opentelemetry.instrumentation.boto import BotoInstrumentor
    from opentelemetry.instrumentation.botocore import BotocoreInstrumentor

    from lumigo_wrapper.instrumentations.botocore.botocore_instrumentation import (
        AwsParser,
    )

    BotocoreInstrumentor().instrument(
        request_hook=AwsParser.request_hook,
        response_hook=AwsParser.response_hook,
    )
    BotoInstrumentor().instrument()
except ImportError:
    pass
