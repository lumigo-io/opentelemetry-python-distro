import json
import logging
import os
import sys
import urllib.request
from typing import Any, Dict, Optional

from opentelemetry.sdk.extension.aws.resource.ecs import AwsEcsResourceDetector
from opentelemetry.sdk.extension.aws.resource.eks import AwsEksResourceDetector
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
from lumigo_opentelemetry.libs.json_utils import dump_with_context

logger = logging.getLogger(__name__)


LUMIGO_DISTRO_VERSION_ATTR_NAME = "lumigo.distro.version"
LUMIGO_TAG_ATTR_NAME = "lumigo.tag"
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


class LumigoTagDetector(ResourceDetector):
    def detect(self) -> "Resource":
        lumigo_tag = os.environ.get("LUMIGO_TAG")
        if not lumigo_tag:
            return Resource.get_empty()
        if ";" in lumigo_tag:
            logger.warning(
                "LUMIGO_TAG contains a semicolon, which is not allowed.",
                extra={"lumigo_tag": lumigo_tag},
            )
            return Resource.get_empty()
        return Resource(
            {
                LUMIGO_TAG_ATTR_NAME: lumigo_tag,
            }
        )


class LumigoContainerNameDetector(ResourceDetector):
    def detect(self) -> "Resource":
        container_name = os.environ.get("LUMIGO_CONTAINER_NAME")
        if not container_name:
            return Resource.get_empty()
        return Resource(
            {
                ResourceAttributes.K8S_CONTAINER_NAME: container_name,
            }
        )


class EnvVarsDetector(ResourceDetector):
    def detect(self) -> "Resource":
        return Resource(
            {ENV_ATTR_NAME: dump_with_context("environment", dict(os.environ))}
        )


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


#
# Kubernetes Pod UUID, based on https://github.com/open-telemetry/opentelemetry-python-contrib/pull/1489
#

_POD_ID_LENGTH = 36
_CONTAINER_ID_LENGTH = 64


def is_container_on_kubernetes() -> bool:
    # Kubernetes manages the /etc/hosts file inside the pods' containers,
    # using a distinctive header, see https://github.com/kubernetes/kubernetes/commit/fd72938dd569bd041f11a76eecfe9b8b4bcf5ae8
    with open("/etc/hosts", "r", encoding="utf8") as hosts_file:
        first_line = hosts_file.readline()
        return first_line.startswith("# Kubernetes-managed hosts file")


def get_kubenertes_pod_uid_v1() -> Optional[str]:
    pod_id = None
    with open("/proc/self/mountinfo", "r", encoding="utf8") as container_info_file:
        for raw_line in container_info_file.readlines():
            line = raw_line.strip()
            # Subsequent IDs should be the same, exit if found one
            if len(line) > _POD_ID_LENGTH and "/pods/" in line:
                pod_id = line.split("/pods/")[1][:_POD_ID_LENGTH]
                break
    return pod_id


def get_kubenertes_pod_uid_v2() -> Optional[str]:
    pod_id = None
    with open("/proc/self/cgroup", "r", encoding="utf8") as container_info_file:
        for raw_line in container_info_file.readlines():
            line = raw_line.strip()
            # Subsequent IDs should be the same, exit if found one
            if len(line) > _CONTAINER_ID_LENGTH:
                line_info = line.split("/")
                if (
                    len(line_info) > 2
                    and line_info[-2][:3] == "pod"
                    and len(line_info[-2]) == _POD_ID_LENGTH + 3
                ):
                    pod_id = line_info[-2][3 : 3 + _POD_ID_LENGTH]  # noqa: E203
                else:
                    pod_id = line_info[-2]
                break
    return pod_id


class LumigoKubernetesResourceDetector(ResourceDetector):
    """Detects attribute values only available when the app is running on kubernetes
    container and returns a resource object.
    """

    def detect(self) -> "Resource":
        if is_container_on_kubernetes():
            try:
                pod_uid = get_kubenertes_pod_uid_v1() or get_kubenertes_pod_uid_v2()
                if pod_uid:
                    return Resource(
                        {
                            ResourceAttributes.K8S_POD_UID: pod_uid,
                        }
                    )
            except Exception as exception:
                logger.warning(
                    "Failed to get pod ID on kubernetes container: %s.",
                    exception,
                )

        return Resource.get_empty()


def get_infrastructure_resource() -> "Resource":
    return get_aggregated_resources(
        detectors=[
            OTELResourceDetector(),
            LumigoDistroDetector(),
            LumigoTagDetector(),
            LumigoContainerNameDetector(),
            LumigoAwsEcsResourceDetector(),
            LumigoKubernetesResourceDetector(),
            AwsEcsResourceDetector(),
            AwsEksResourceDetector(),
        ],
    )


def get_process_resource() -> "Resource":
    return get_aggregated_resources(
        detectors=[
            EnvVarsDetector(),
            ProcessResourceDetector(),
        ],
    )


def get_resource(
    infrastructure_resource: "Resource",
    process_resource: "Resource",
    attributes: Dict[str, Any],
) -> "Resource":
    return (
        Resource.create(attributes=attributes)
        .merge(process_resource)
        .merge(infrastructure_resource)
    )
