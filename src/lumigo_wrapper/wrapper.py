from __future__ import annotations

import json
import os
import uuid
from enum import Enum
from platform import python_version
from typing import Optional, Callable, Any, Union, Dict

import requests
from lumigo_wrapper.libs.json_utils import dump
from lumigo_wrapper.parsers.botocore_parser import AwsParser
from lumigo_wrapper.parsers.fastapi_parser import FastAPIParser
from lumigo_wrapper.lumigo_utils import get_logger
from lumigo_wrapper.parsers.http_parser import HttpParser
from opentelemetry import trace
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.boto import BotoInstrumentor
from opentelemetry.instrumentation.botocore import BotocoreInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.exporter.zipkin.json import ZipkinExporter
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource
from flask import Flask
from fastapi import FastAPI

LUMIGO_ENDPOINT = "https://ga-otlp.lumigo-tracer-edge.golumigo.com/"
LUMIGO_ENDPOINT_SUFFIX = "api/spans"
ZIPKIN = "zipkin"

CONTEXT_NAME = "lumigo_wrapper"
PARENT_IDENTICATOR = "LumigoParentSpan"

metadata_cache: Dict[str, str] = {}


class Framework(Enum):
    Flask = "flask"
    FastAPI = "fast-api"
    Unknown = "unknown"

    @staticmethod
    def from_resource(resource: Any) -> Framework:
        if isinstance(resource, Flask):
            return Framework.Flask
        if isinstance(resource, FastAPI):
            return Framework.FastAPI
        return Framework.Unknown

    @staticmethod
    def safe_from_resource(resource: Any) -> Framework:
        try:
            return Framework.from_resource(resource=resource)
        except Exception:
            return Framework.Unknown


def safe_get_version() -> str:
    try:
        return python_version()
    except Exception as e:
        get_logger().exception("failed getting python version", exc_info=e)
        return ""


def safe_get_metadata() -> str:
    try:
        metadata_uri = os.environ.get("ECS_CONTAINER_METADATA_URI")
        if not metadata_uri:
            return ""
        if metadata_cache.get(metadata_uri):
            return metadata_cache[metadata_uri]
        metadata_cache[metadata_uri] = requests.get(metadata_uri).text
        return metadata_cache[metadata_uri]
    except Exception as e:
        get_logger().exception("failed to fetch ecs metadata", exc_info=e)
        return ""


def safe_get_envs() -> str:
    try:
        return json.dumps(dict(os.environ))
    except Exception as e:
        get_logger().exception("failed getting envs", exc_info=e)
        return ""


def lumigo_wrapper(
    lumigo_token: str,
    service_name: str,
    resource: Optional[Union[Flask, FastAPI]] = None,
    endpoint: str = None,
    global_thread_safe: bool = False,
) -> Optional[Callable]:
    """
    This is the wrapper line that should be called when tracing a distributed system.

    :param lumigo_token: The token to use when sending data to Lumigo.
    :param service_name: The logical name of this unit.
    :param resource: A framework-specific resource that we should wrap. See Lumigo's docs for more details.
    :param endpoint: Optional custom endpoint to alter the default collector.
    :param global_thread_safe: Optional flag to indicates that calls may be executed in threads. This flag
        creates a single parent to all the span in the current interpreter.
    """
    zipkin_processor = BatchSpanProcessor(
        ZipkinExporter(
            endpoint=endpoint or f"{LUMIGO_ENDPOINT}{LUMIGO_ENDPOINT_SUFFIX}"
        )
    )
    attributes = {
        "lumigoToken": lumigo_token,
        "service.name": service_name,
        "runtime": f"python{safe_get_version()}",
        "framework": Framework.safe_from_resource(resource=resource).value,
        "envs": safe_get_envs(),
        "metadata": safe_get_metadata(),
        "exporter": ZIPKIN,
    }
    if global_thread_safe:
        attributes["globalTransactionId"] = f"c_{uuid.uuid4().hex}"
        attributes["globalParentId"] = uuid.uuid4().hex
    tracer_resource = Resource(attributes=attributes)
    tracer_provider = TracerProvider(resource=tracer_resource)
    tracer_provider.add_span_processor(zipkin_processor)
    trace.set_tracer_provider(tracer_provider)

    to_return = None
    if isinstance(resource, Flask):
        FlaskInstrumentor().instrument_app(resource)
    elif isinstance(resource, FastAPI):
        FastAPIInstrumentor().instrument_app(
            resource,
            server_request_hook=FastAPIParser.server_request_hook,
            client_request_hook=FastAPIParser.client_request_hook,
            client_response_hook=FastAPIParser.client_response_hook,
        )
    elif callable(resource):

        def wrapped(*args, **kwargs):
            tracer = tracer_provider.get_tracer(CONTEXT_NAME)
            with tracer.start_as_current_span(PARENT_IDENTICATOR) as span:
                span.set_attribute("input_args", dump(args))
                span.set_attribute("input_kwargs", dump(kwargs))
                retval = resource(*args, **kwargs)
                span.set_attribute("return_value", dump(retval))
            return retval

        to_return = wrapped

    RequestsInstrumentor().instrument(span_callback=HttpParser.request_callback)
    BotocoreInstrumentor().instrument(
        request_hook=AwsParser.request_hook, response_hook=AwsParser.response_hook
    )
    BotoInstrumentor().instrument()
    return to_return
