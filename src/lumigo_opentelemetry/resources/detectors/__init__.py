from opentelemetry.semconv.resource import ResourceAttributes
from opentelemetry.sdk.resources import *;

from logging import getLogger

import os
import requests
import sys

AWS_ECS_CLUSTER_ARN = ResourceAttributes.AWS_ECS_CLUSTER_ARN
AWS_ECS_CONTAINER_ARN = ResourceAttributes.AWS_ECS_CONTAINER_ARN
AWS_ECS_LAUNCHTYPE = ResourceAttributes.AWS_ECS_LAUNCHTYPE
AWS_ECS_TASK_ARN = ResourceAttributes.AWS_ECS_TASK_ARN
AWS_ECS_TASK_FAMILY = ResourceAttributes.AWS_ECS_TASK_FAMILY
AWS_ECS_TASK_REVISION = ResourceAttributes.AWS_ECS_TASK_REVISION


_aws_ecs_detector_logger = getLogger('AwsEcsResourceDetector')


class AwsEcsResourceDetector(ResourceDetector):
    """Implements the lookup of the `aws.ecs` resource attributes using the Metadata v4 endpoint."""

    # pylint: disable=no-self-use
    def detect(self) -> "Resource":
        metadataEndpoint = os.environ.get('ECS_CONTAINER_METADATA_URI_V4')

        if not metadataEndpoint:
            return Resource.get_empty()

        try:
            # Returns https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task-metadata-endpoint-v4.html#task-metadata-endpoint-v4-response
            metadataContainerResponse = requests.get(metadataEndpoint, timeout=1)
            metadataContainerResponse.raise_for_status()
            metadataContainer = metadataContainerResponse.json()

            metadataTaskResponse = requests.get(f"{metadataEndpoint}/task", timeout=1)
            metadataTaskResponse.raise_for_status()
            metadataTask = metadataTaskResponse.json()

            taskArn = metadataTask['TaskARN']
            baseArn = taskArn[0: taskArn.rindex(':')]

            cluster = metadataTask['Cluster']

            try:
                if cluster.index('arn:') == 0:
                    clusterArn = cluster
            except ValueError:
                # Cluster is the shortname
                clusterArn = f"{baseArn}:cluster/{cluster}"

            return Resource(
                {
                    AWS_ECS_CLUSTER_ARN: clusterArn,
                    AWS_ECS_CONTAINER_ARN: metadataContainer['ContainerARN'],
                    AWS_ECS_LAUNCHTYPE: metadataTask['LaunchType'],
                    AWS_ECS_TASK_ARN: taskArn,
                    AWS_ECS_TASK_FAMILY: metadataTask['Family'],
                    AWS_ECS_TASK_REVISION: metadataTask['Revision'],
                }
            )
        except Exception as e:
            _aws_ecs_detector_logger.error("An error occurred while looking up the AWS ECS resource attributes: %s", e)

            return Resource.get_empty()

"""TODO: Switch over to https://github.com/open-telemetry/opentelemetry-python/blob/main/opentelemetry-sdk/src/opentelemetry/sdk/resources/__init__.py on SDK upgrade"""
class ProcessResourceDetector(ResourceDetector):
    """Implementation of the detector for `process.*` attributes.
    """

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