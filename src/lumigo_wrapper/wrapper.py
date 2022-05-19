from __future__ import annotations

import os
from platform import python_version
from typing import Dict

import requests

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.exporter.zipkin.json import ZipkinExporter
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource

from lumigo_wrapper.instrumentations.instrumentations import Framework, frameworks
from lumigo_wrapper.libs.json_utils import dump
from lumigo_wrapper.lumigo_utils import get_logger

import lumigo_wrapper.instrumentations  # noqa


LUMIGO_ENDPOINT = "https://ga-otlp.lumigo-tracer-edge.golumigo.com/"
LUMIGO_ENDPOINT_SUFFIX = "api/spans"
ZIPKIN = "zipkin"


metadata_cache: Dict[str, str] = {}


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
        return dump(dict(os.environ))
    except Exception as e:
        get_logger().exception("failed getting envs", exc_info=e)
        return ""


attributes = {
    "lumigoToken": os.environ["LUMIGO_TRACER_TOKEN"],
    "runtime": f"python{safe_get_version()}",
    "framework": frameworks[0].value if frameworks else Framework.Unknown.value,
    "envs": safe_get_envs(),
    "metadata": safe_get_metadata(),
    "exporter": ZIPKIN,
}
tracer_resource = Resource(attributes=attributes)

span_processor = BatchSpanProcessor(
    ZipkinExporter(endpoint="http://localhost:9411/api/v2/spans"),
)
tracer_provider = TracerProvider(resource=tracer_resource)
tracer_provider.add_span_processor(span_processor)
trace.set_tracer_provider(tracer_provider)

CONTEXT_NAME = "lumigo_wrapper"
PARENT_IDENTICATOR = "LumigoParentSpan"


def lumigo_wrapped(func):
    def wrapper(*args, **kwargs):
        tracer = tracer_provider.get_tracer(CONTEXT_NAME)
        with tracer.start_as_current_span(PARENT_IDENTICATOR) as span:
            span.set_attribute("input_args", dump(args))
            span.set_attribute("input_kwargs", dump(kwargs))
            return_value = func(*args, **kwargs)
            span.set_attribute("return_value", dump(return_value))
            return return_value

    return wrapper
