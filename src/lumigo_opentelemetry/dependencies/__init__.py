from http.client import HTTPSConnection
from json import dumps
from os import environ
from pkg_resources import Environment, get_distribution
from typing import Any, Dict
from urllib.parse import urlparse

from lumigo_opentelemetry import logger
from opentelemetry.attributes import BoundedAttributes

DEFAULT_CONNECTION_TIMEOUT = 3


def report(url: str, lumigo_token: str, resource_attributes: BoundedAttributes):
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


def _report_to_saas(url: str, lumigo_token: str, data: str):
    parsed_url = urlparse(url)
    timeout = environ.get("LUMIGO_CONNECTION_TIMEOUT", DEFAULT_CONNECTION_TIMEOUT)

    try:
        connection = HTTPSConnection(parsed_url.hostname, timeout=timeout)
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
            logger.debug(
                "Dependency report failed with status code %s", response_status
            )
    except Exception as e:
        logger.debug("Dependency report failed", e)
