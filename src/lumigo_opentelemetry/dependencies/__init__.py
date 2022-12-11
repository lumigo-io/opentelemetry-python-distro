# To provide better support and better data-driven product decisions
# with respect to which packages to support next, the Lumigo
# OpenTelemetry Distro for Python will report to Lumigo on startup the
# packages and their versions used in this application, together with the
# OpenTelemetry resource data to enable analytics in terms of which platforms
# use which dependencies.
#
# This behavior is opt-out using the `LUMIGO_REPORT_DEPENDENCIES=false`
# environment variable.

from json import dumps
from pkg_resources import Environment, get_distribution
from typing import Any, Dict

from opentelemetry.attributes import BoundedAttributes
import requests

from lumigo_opentelemetry.utils.config import get_connection_timeout_seconds


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
    response = requests.post(
        url,
        data=data,
        headers={
            "Authorization": f"LumigoToken {lumigo_token}",
            "Content-type": "application/json",
        },
        timeout=get_connection_timeout_seconds(),
    )

    response_status = response.status_code

    if response_status != 200:
        raise Exception(
            f"Dependency report failed with status code {response_status}; response body: {response.text}"
        )
