try:
    import flask  # noqa
    import wrapt
    from lumigo_wrapper.lumigo_utils import get_logger
    from lumigo_wrapper.instrumentations.instrumentations import Framework, frameworks

    @wrapt.patch_function_wrapper("flask", "Flask.__init__")
    def init_otel_flask_instrumentation(wrapped, instance, args, kwargs):
        try:
            from opentelemetry.instrumentation.flask import FlaskInstrumentor

            return_value = wrapped(*args, **kwargs)
            FlaskInstrumentor().instrument_app(instance)
            frameworks.append(Framework.Flask)
            return return_value
        except Exception as e:
            get_logger().exception("failed instrumenting Flask", exc_info=e)


except ImportError:
    pass
