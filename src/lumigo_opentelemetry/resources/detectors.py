import os
import sys

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


def get_resource(attributes: dict) -> "Resource":
    return get_aggregated_resources(
        detectors=[
            OTELResourceDetector(),
            EnvVarsDetector(),
            ProcessResourceDetector(),
            LumigoDistroDetector(),
            AwsEcsResourceDetector(),
        ],
        initial_resource=Resource.create(attributes=attributes),
    )
