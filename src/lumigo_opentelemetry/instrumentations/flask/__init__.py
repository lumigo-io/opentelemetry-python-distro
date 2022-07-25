from lumigo_opentelemetry.instrumentations import AbstractInstrumentor

class FlaskInstrumentor(AbstractInstrumentor):
    def __init__(self):
        super().__init__("flask")

    def get_otel_instrumentor(self):
        from opentelemetry.instrumentation.flask import (
            FlaskInstrumentor as UpstreamInstrumentor,
        )

        return UpstreamInstrumentor()

    def _do_instrument(self, instrumentor):
        import wrapt
        from lumigo_opentelemetry import logger

        @wrapt.patch_function_wrapper("flask", "Flask.__init__")
        def init_otel_flask_instrumentation(wrapped, instance, args, kwargs):  # type: ignore
            try:
                return_value = wrapped(*args, **kwargs)
                instrumentor.instrument_app(instance)
                return return_value
            except Exception as e:
                logger.exception("failed instrumenting Flask", exc_info=e)
