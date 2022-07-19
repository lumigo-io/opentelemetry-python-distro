import json
import os

import pytest
from opentelemetry.sdk import resources

from lumigo_opentelemetry.resources.detectors import (
    ProcessResourceDetector,
    LumigoDistroDetector,
    EnvVarsDetector,
    get_resource,
)


@pytest.fixture(autouse=True)
def keep_env_vars():
    original_environ = os.environ.copy()
    yield
    os.environ.clear()
    os.environ.update(original_environ)


def test_process_detector():
    initial_resource = resources.Resource({"foo": "bar"})
    aggregated_resource = resources.get_aggregated_resources(
        [ProcessResourceDetector()], initial_resource
    )

    assert aggregated_resource.attributes[resources.PROCESS_RUNTIME_NAME] == "cpython"
    assert aggregated_resource.attributes[resources.PROCESS_RUNTIME_VERSION].startswith(
        "3."
    )
    assert resources.PROCESS_RUNTIME_DESCRIPTION in aggregated_resource.attributes


def test_lumigo_distro_version_detect():
    resource = LumigoDistroDetector().detect()
    major, minor, patch = resource.attributes["lumigo.distro.version"].split(".")
    assert major.isdigit()
    assert minor.isdigit()
    assert patch.isdigit()


def test_env_vars_detector():
    os.environ.clear()
    envs = {"a": "b", "k": "v"}
    os.environ.update(envs)

    resource = EnvVarsDetector().detect()

    assert resource.attributes["process.environ"] == json.dumps(envs)


def test_get_resource_aws_ecs_resource_detector():
    os.environ["ECS_CONTAINER_METADATA_URI"] = "mock-url"

    resource = get_resource({"a": "b"})

    assert resource.attributes["cloud.provider"] == "aws"
    assert resource.attributes["cloud.platform"] == "aws_ecs"
    assert isinstance(resource.attributes["container.name"], str)
    assert len(resource.attributes["container.name"]) > 1
    assert isinstance(resource.attributes["container.id"], str)
