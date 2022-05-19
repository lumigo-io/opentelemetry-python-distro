try:
    import fastapi  # noqa

    import lumigo_wrapper.instrumentations.fastapi.fastapi_instrumentation  # noqa
except ImportError:
    pass
