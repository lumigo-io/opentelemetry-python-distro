# To provide better support and better data-driven product decisions
# with respect to which packages to support next, the Lumigo
# OpenTelemetry Distro for Python will report to Lumigo on startup the
# packages and their versions used in this application, together with the
# OpenTelemetry resource data to enable analytics in terms of which platforms
# use which dependencies.
#
# This behavior is opt-out using the `LUMIGO_REPORT_DEPENDENCIES=false`
# environment variable.

from http.client import HTTPSConnection
from json import dumps
from os import environ
from pkg_resources import Environment, get_distribution
from typing import Any, Dict
from urllib.parse import urlparse

from opentelemetry.attributes import BoundedAttributes

DEFAULT_CONNECTION_TIMEOUT = 3


def report(url: str, lumigo_token: str, resource_attributes: BoundedAttributes) -> None:
    dependencies = [
        {
            "name": distribution_name,
            "version": get_distribution(distribution_name).version,
        }
        for distribution_name in Environment()
    ]

    data = dumps(
        {
            "resourceAttributes": _prepare_resource_attributes_for_marshalling(
                resource_attributes
            ),
            "dependencies": dependencies,
        }
    )

    _report_to_saas(url, lumigo_token, data)


def _prepare_resource_attributes_for_marshalling(
    resource_attributes: BoundedAttributes,
) -> Dict[str, Any]:
    return {
        attribute_name: resource_attributes[attribute_name]
        for attribute_name in resource_attributes.keys()
    }


def _report_to_saas(url: str, lumigo_token: str, data: str) -> None:
    parsed_url = urlparse(url)
    timeout = environ.get("LUMIGO_CONNECTION_TIMEOUT", DEFAULT_CONNECTION_TIMEOUT)

    connection = HTTPSConnection(parsed_url.hostname or "", timeout=float(timeout))
    connection.request(
        "POST",
        parsed_url.path,
        data,
        {
            "Authorization": f"LumigoToken {lumigo_token}",
            "Content-type": "application/json",
        },
    )

    response = connection.getresponse()
    response_status = response.status

    if response_status != 200:
        raise Exception(f"Dependency report failed with status code {response_status}")
