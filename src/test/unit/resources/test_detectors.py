import json
import os

from opentelemetry.sdk import resources
import pytest
import responses

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

    resource = get_resource({})

    assert resource.attributes["cloud.provider"] == "aws"
    assert resource.attributes["cloud.platform"] == "aws_ecs"
    assert isinstance(resource.attributes["container.name"], str)
    assert len(resource.attributes["container.name"]) > 1
    assert isinstance(resource.attributes["container.id"], str)


def load_json(filename: str):
    with open(os.path.join(os.path.dirname(__file__), filename)) as f:
        return json.load(f)


@responses.activate
def test_get_resource_lumigo_aws_ecs_resource_detector(monkeypatch):
    aws_ecs_metadata_url = "http://test.uri.ecs"
    responses.add(
        method="GET",
        url=aws_ecs_metadata_url,
        json=load_json("metadatav4-response-container.json"),
    )
    responses.add(
        method="GET",
        url=f"{aws_ecs_metadata_url}/task",
        json=load_json("metadatav4-response-task.json"),
    )
    monkeypatch.setenv("ECS_CONTAINER_METADATA_URI_V4", aws_ecs_metadata_url)

    resource = get_resource({})

    assert (
        resource.attributes["aws.ecs.container.arn"]
        == "arn:aws:ecs:us-west-2:111122223333:container/0206b271-b33f-47ab-86c6-a0ba208a70a9"
    )
    assert (
        resource.attributes["aws.ecs.cluster.arn"]
        == "arn:aws:ecs:us-west-2:111122223333:cluster/default"
    )
    assert resource.attributes["aws.ecs.launchtype"] == "EC2"
    assert (
        resource.attributes["aws.ecs.task.arn"]
        == "arn:aws:ecs:us-west-2:111122223333:task/default/158d1c8083dd49d6b527399fd6414f5c"
    )
    assert resource.attributes["aws.ecs.task.family"] == "curltest"
    assert resource.attributes["aws.ecs.task.revision"] == "26"
