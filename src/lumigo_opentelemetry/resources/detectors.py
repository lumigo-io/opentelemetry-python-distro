import json
import os
import sys
import urllib.request
from typing import List, Dict, Any

from opentelemetry.sdk.extension.aws.resource.ecs import AwsEcsResourceDetector
from opentelemetry.sdk.resources import (
    ResourceDetector,
    Resource,
    PROCESS_RUNTIME_DESCRIPTION,
    PROCESS_RUNTIME_NAME,
    PROCESS_RUNTIME_VERSION,
    OTELResourceDetector,
    get_aggregated_resources,
)
from opentelemetry.semconv.resource import ResourceAttributes

import lumigo_opentelemetry
from lumigo_opentelemetry.libs.json_utils import dump

LUMIGO_DISTRO_VERSION_ATTR_NAME = "lumigo.distro.version"
ENV_ATTR_NAME = "process.environ"


# TODO: ProcessResourceDetector will be part of the next release of opentelemetry-sdk. After the release - delete it.
class ProcessResourceDetector(ResourceDetector):
    # pylint: disable=no-self-use
    def detect(self) -> "Resource":
        _runtime_version = ".".join(
            map(
                str,
                sys.version_info[:3]
                if sys.version_info.releaselevel == "final"
                and not sys.version_info.serial
                else sys.version_info,
            )
        )

        return Resource(
            {
                PROCESS_RUNTIME_DESCRIPTION: sys.version,
                PROCESS_RUNTIME_NAME: sys.implementation.name,
                PROCESS_RUNTIME_VERSION: _runtime_version,
            }
        )


class LumigoDistroDetector(ResourceDetector):
    def detect(self) -> "Resource":
        return Resource(
            {
                LUMIGO_DISTRO_VERSION_ATTR_NAME: lumigo_opentelemetry.__version__,
            }
        )


class EnvVarsDetector(ResourceDetector):
    def detect(self) -> "Resource":
        return Resource({ENV_ATTR_NAME: dump(dict(os.environ))})


class LumigoAwsEcsResourceDetector(ResourceDetector):
    """Implements the lookup of the `aws.ecs` resource attributes using the Metadata v4 endpoint."""

    @staticmethod
    def _http_get(url: str) -> Dict[Any, Any]:
        with urllib.request.urlopen(url, timeout=1) as response:
            return json.loads(response.read().decode())  # type: ignore

    def detect(self) -> "Resource":
        metadata_endpoint = os.environ.get("ECS_CONTAINER_METADATA_URI_V4")

        if not metadata_endpoint:
            return Resource.get_empty()

        # Returns https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task-metadata-endpoint-v4.html#task-metadata-endpoint-v4-response
        metadata_container = LumigoAwsEcsResourceDetector._http_get(metadata_endpoint)
        metadata_task = LumigoAwsEcsResourceDetector._http_get(
            f"{metadata_endpoint}/task"
        )

        task_arn = metadata_task["TaskARN"]
        base_arn = task_arn[0 : task_arn.rindex(":")]  # noqa
        cluster: str = metadata_task["Cluster"]
        cluster_arn = (
            cluster if cluster.startswith("arn:") else f"{base_arn}:cluster/{cluster}"
        )

        return Resource(
            {
                ResourceAttributes.AWS_ECS_CLUSTER_ARN: cluster_arn,
                ResourceAttributes.AWS_ECS_CONTAINER_ARN: metadata_container[
                    "ContainerARN"
                ],
                ResourceAttributes.AWS_ECS_LAUNCHTYPE: metadata_task["LaunchType"],
                ResourceAttributes.AWS_ECS_TASK_ARN: task_arn,
                ResourceAttributes.AWS_ECS_TASK_FAMILY: metadata_task["Family"],
                ResourceAttributes.AWS_ECS_TASK_REVISION: metadata_task["Revision"],
            }
        )


def get_resource(attributes: Dict[str, Any]) -> "Resource":
    return get_aggregated_resources(
        detectors=_get_detector_list(),
        initial_resource=Resource.create(attributes=attributes),
    )


def _get_detector_list() -> List[ResourceDetector]:
    return [
        OTELResourceDetector(),
        EnvVarsDetector(),
        ProcessResourceDetector(),
        LumigoDistroDetector(),
        LumigoAwsEcsResourceDetector(),
        AwsEcsResourceDetector(),
    ]
