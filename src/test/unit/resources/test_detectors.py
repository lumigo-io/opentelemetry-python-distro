import json
import os
import urllib.request
from contextlib import contextmanager

from opentelemetry.sdk import resources
from opentelemetry.semconv.resource import ResourceAttributes

from lumigo_opentelemetry.resources.detectors import (
    ProcessResourceDetector,
    LumigoDistroDetector,
    EnvVarsDetector,
    get_resource,
)


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


def test_env_vars_detector(monkeypatch):
    for key in os.environ:
        monkeypatch.delenv(key)
    monkeypatch.setenv("a", "b")
    monkeypatch.setenv("k", "v")

    resource = EnvVarsDetector().detect()

    assert resource.attributes["process.environ"] == json.dumps({"a": "b", "k": "v"})


def test_get_resource_aws_ecs_resource_detector(monkeypatch):
    monkeypatch.setenv("ECS_CONTAINER_METADATA_URI", "mock-url")

    resource = get_resource({})

    assert resource.attributes[ResourceAttributes.CLOUD_PROVIDER] == "aws"
    assert resource.attributes[ResourceAttributes.CLOUD_PLATFORM] == "aws_ecs"
    assert isinstance(resource.attributes[ResourceAttributes.CONTAINER_NAME], str)
    assert len(resource.attributes[ResourceAttributes.CONTAINER_NAME]) > 1
    assert isinstance(resource.attributes[ResourceAttributes.CONTAINER_ID], str)


@contextmanager
def mocked_urlopen(url: str, timeout: int):
    filename = (
        "metadatav4-response-task.json"
        if url.endswith("/task")
        else "metadatav4-response-container.json"
    )
    with open(os.path.join(os.path.dirname(__file__), filename), "rb") as f:
        yield f


def test_get_resource_lumigo_aws_ecs_resource_detector(monkeypatch, caplog):
    aws_ecs_metadata_url = "http://test.uri.ecs"
    monkeypatch.setattr(urllib.request, "urlopen", mocked_urlopen)
    monkeypatch.setenv("ECS_CONTAINER_METADATA_URI_V4", aws_ecs_metadata_url)

    resource = get_resource({})

    assert (
        resource.attributes[ResourceAttributes.AWS_ECS_CONTAINER_ARN]
        == "arn:aws:ecs:us-west-2:111122223333:container/0206b271-b33f-47ab-86c6-a0ba208a70a9"
    )
    assert (
        resource.attributes[ResourceAttributes.AWS_ECS_CLUSTER_ARN]
        == "arn:aws:ecs:us-west-2:111122223333:cluster/default"
    )
    assert resource.attributes[ResourceAttributes.AWS_ECS_LAUNCHTYPE] == "EC2"
    assert (
        resource.attributes[ResourceAttributes.AWS_ECS_TASK_ARN]
        == "arn:aws:ecs:us-west-2:111122223333:task/default/158d1c8083dd49d6b527399fd6414f5c"
    )
    assert resource.attributes[ResourceAttributes.AWS_ECS_TASK_FAMILY] == "curltest"
    assert resource.attributes[ResourceAttributes.AWS_ECS_TASK_REVISION] == "26"


def test_get_resource_lumigo_aws_ecs_resource_detector_with_exception(
    monkeypatch, caplog
):
    monkeypatch.setattr(urllib.request, "urlopen", lambda *args, **kwargs: 1 / 0)
    monkeypatch.setenv("ECS_CONTAINER_METADATA_URI_V4", "http://test.uri.ecs")

    resource = get_resource({})

    assert resource.attributes[resources.PROCESS_RUNTIME_NAME] == "cpython"
    assert ResourceAttributes.AWS_ECS_CONTAINER_ARN not in resource.attributes
    assert list(
        filter(
            lambda record: "division by zero" in record.message
            and "LumigoAwsEcsResourceDetector" in record.message,
            caplog.records,
        )
    )
