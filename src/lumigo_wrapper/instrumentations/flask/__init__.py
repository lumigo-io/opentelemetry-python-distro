try:
    import flask  # noqa

    from lumigo_wrapper.instrumentations.flask import flask_instrumentation  # noqa
except ImportError:
    pass
