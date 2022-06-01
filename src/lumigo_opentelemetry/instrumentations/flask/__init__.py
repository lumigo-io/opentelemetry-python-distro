from lumigo_opentelemetry.instrumentations import AbstractInstrumentor


class FlaskInstrumentorWrapper(AbstractInstrumentor):
    def __init__(self):
        super().__init__("flask")

    def check_if_applicable(self):
        import flask  # noqa

    def install_instrumentation(self):
        import wrapt
        from lumigo_opentelemetry import logger

        @wrapt.patch_function_wrapper("flask", "Flask.__init__")
        def init_otel_flask_instrumentation(wrapped, instance, args, kwargs):
            try:
                from opentelemetry.instrumentation.flask import FlaskInstrumentor

                return_value = wrapped(*args, **kwargs)
                FlaskInstrumentor().instrument_app(instance)
                return return_value
            except Exception as e:
                logger.exception("failed instrumenting Flask", exc_info=e)


instrumentor: AbstractInstrumentor = FlaskInstrumentorWrapper()
