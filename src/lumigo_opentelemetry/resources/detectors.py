import sys

from opentelemetry.sdk.resources import (
    ResourceDetector,
    Resource,
    PROCESS_RUNTIME_DESCRIPTION,
    PROCESS_RUNTIME_NAME,
    PROCESS_RUNTIME_VERSION,
)


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
