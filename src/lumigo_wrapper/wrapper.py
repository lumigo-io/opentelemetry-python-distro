from __future__ import annotations

import os
import uuid
from platform import python_version
from typing import Optional, Callable, Any, Dict

import requests

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.exporter.zipkin.json import ZipkinExporter
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource

from lumigo_wrapper.instrumentations.instrumentations import (
    enforce_instrumentations,
    Framework,
)
from lumigo_wrapper.libs.json_utils import dump
from lumigo_wrapper.lumigo_utils import get_logger


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


def lumigo_wrapper(
    lumigo_token: str,
    service_name: str,
    resource: Optional[Any] = None,
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

    return enforce_instrumentations(tracer_provider=tracer_provider, resource=resource)
