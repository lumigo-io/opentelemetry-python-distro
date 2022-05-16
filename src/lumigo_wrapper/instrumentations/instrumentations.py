from __future__ import annotations

from enum import Enum
from typing import Optional, Any

from opentelemetry.sdk.trace import TracerProvider

from lumigo_wrapper.libs.json_utils import dump
from lumigo_wrapper.instrumentations.fastapi.fastapi import FastAPI
from lumigo_wrapper.instrumentations.flask.flask import Flask
from lumigo_wrapper.instrumentations.http.http import Requests
from lumigo_wrapper.instrumentations.botocore.botocore import Botocore

CONTEXT_NAME = "lumigo_wrapper"
PARENT_IDENTICATOR = "LumigoParentSpan"


def enforce_instrumentations(
    tracer_provider: TracerProvider, resource: Any
) -> Optional[Any]:
    to_return = None

    FastAPI.instrument(resource=resource)
    Flask.instrument(resource=resource)
    Requests.instrument()
    Botocore.instrument()

    if callable(resource):

        def wrapped(*args, **kwargs):
            tracer = tracer_provider.get_tracer(CONTEXT_NAME)
            with tracer.start_as_current_span(PARENT_IDENTICATOR) as span:
                span.set_attribute("input_args", dump(args))
                span.set_attribute("input_kwargs", dump(kwargs))
                retval = resource(*args, **kwargs)
                span.set_attribute("return_value", dump(retval))
            return retval

        to_return = wrapped

    return to_return


class Framework(Enum):
    Flask = "flask"
    FastAPI = "fast-api"
    Unknown = "unknown"

    @staticmethod
    def from_resource(resource: Any) -> Framework:
        if Flask.is_flask(resource=resource):
            return Framework.Flask
        if FastAPI.is_fastapi(resource):
            return Framework.FastAPI
        return Framework.Unknown

    @staticmethod
    def safe_from_resource(resource: Any) -> Framework:
        try:
            return Framework.from_resource(resource=resource)
        except Exception:
            return Framework.Unknown
