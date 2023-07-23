import json
import os
import re
import urllib.request
from contextlib import contextmanager

from mock_open import MockOpen
from mock import patch
from opentelemetry.sdk import resources
from opentelemetry.semconv.resource import ResourceAttributes
from lumigo_core.configuration import CoreConfiguration

from lumigo_opentelemetry.resources.detectors import (
    ProcessResourceDetector,
    LumigoDistroDetector,
    LumigoKubernetesResourceDetector,
    EnvVarsDetector,
    get_resource,
    get_infrastructure_resource,
    get_process_resource,
    LumigoTagDetector,
    LumigoContainerNameDetector,
)

from lumigo_opentelemetry import _setup_logger


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


def test_lumigo_tag_detect_not_exist():
    resource = LumigoTagDetector().detect()
    lumigo_tag = resource.attributes.get("lumigo.tag")
    assert not lumigo_tag


def test_lumigo_tag_detect(monkeypatch):
    monkeypatch.setenv("LUMIGO_TAG", "test1234")
    resource = LumigoTagDetector().detect()
    lumigo_tag = resource.attributes.get("lumigo.tag")
    assert lumigo_tag == "test1234"


def test_lumigo_tag_detect_semicolon(monkeypatch, caplog):
    monkeypatch.setenv("LUMIGO_TAG", "test12;34")
    resource = LumigoTagDetector().detect()
    lumigo_tag = resource.attributes.get("lumigo.tag")
    assert not lumigo_tag
    assert (
        caplog.records[0].message
        == "LUMIGO_TAG contains a semicolon, which is not allowed."
    )


def test_lumigo_tag_detect_override_otel_envvar(monkeypatch):
    monkeypatch.setenv("OTEL_RESOURCE_ATTRIBUTES", "lumigo.tag=test9876")
    monkeypatch.setenv("LUMIGO_TAG", "test9876_override")
    resource = get_resource(get_infrastructure_resource(), get_process_resource(), {})
    lumigo_tag = resource.attributes.get("lumigo.tag")
    assert lumigo_tag == "test9876_override"


def test_env_vars_detector(monkeypatch):
    for key in os.environ:
        monkeypatch.delenv(key)
    monkeypatch.setenv("a", "b")
    monkeypatch.setenv("k", "v")
    monkeypatch.setenv("secret", "value")

    resource = EnvVarsDetector().detect()

    assert resource.attributes["process.environ"] == json.dumps(
        {"a": "b", "k": "v", "secret": "****"}
    )


def test_env_vars_detector_specific_config(monkeypatch):
    monkeypatch.setattr(
        CoreConfiguration, "secret_masking_regex_environment", re.compile("specific.*")
    )
    for key in os.environ:
        monkeypatch.delenv(key)
    monkeypatch.setenv("a", "b")
    monkeypatch.setenv("c", "d")
    monkeypatch.setenv("specific_env_var", "value")

    resource = EnvVarsDetector().detect()

    assert resource.attributes["process.environ"] == json.dumps(
        {"a": "b", "c": "d", "specific_env_var": "****"}
    )


def test_get_resource_aws_ecs_resource_detector(monkeypatch):
    monkeypatch.setenv("ECS_CONTAINER_METADATA_URI", "mock-url")

    resource = get_resource(get_infrastructure_resource(), get_process_resource(), {})

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

    resource = get_resource(get_infrastructure_resource(), get_process_resource(), {})

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

    resource = get_resource(get_infrastructure_resource(), get_process_resource(), {})

    assert resource.attributes[resources.PROCESS_RUNTIME_NAME] == "cpython"
    assert ResourceAttributes.AWS_ECS_CONTAINER_ARN not in resource.attributes
    assert list(
        filter(
            lambda record: "division by zero" in record.message
            and "LumigoAwsEcsResourceDetector" in record.message,
            caplog.records,
        )
    )


def test_get_resource_aws_ecs_resource_detector_not_ecs_container(caplog):
    _setup_logger()
    resource = get_resource(get_infrastructure_resource(), get_process_resource(), {})

    assert len(caplog.records) == 0

    assert ResourceAttributes.CLOUD_PLATFORM not in resource.attributes
    assert ResourceAttributes.CLOUD_PLATFORM not in resource.attributes
    assert ResourceAttributes.CONTAINER_NAME not in resource.attributes
    assert ResourceAttributes.CONTAINER_ID not in resource.attributes


K8S_POD_ID = "6189e731-8c9a-4c3a-ba6f-9796664788a8"


def test_kubernetes_detector_not_on_kubernetes():
    mock_open = MockOpen()
    mock_open["/etc/hosts"].read_data = (
        "##\n"
        "# Host Database\n"
        "#\n"
        "# localhost is used to configure the loopback interface\n"
        "# when the system is booting.  Do not change this entry.\n"
        "##\n"
        "127.0.0.1       localhost\n"
        "255.255.255.255 broadcasthost\n"
    )

    with patch("builtins.open", mock_open):
        assert not LumigoKubernetesResourceDetector().detect().attributes


def test_kubernetes_detector_pod_uid_v1():
    mock_open = MockOpen()
    mock_open["/etc/hosts"].read_data = (
        "# Kubernetes-managed hosts file.\n"
        "127.0.0.1       localhost\n"
        "255.255.255.255 broadcasthost\n"
    )
    mock_open["/proc/self/mountinfo"].read_data = (
        "564 446 0:164 / / rw,relatime master:190 - overlay overlay rw,lowerdir=/var/lib/docker/bogusPodIdThatShouldNotBeOneSetBecauseTheFirstOneWasPicked\n"
        "565 564 0:166 / /proc rw,nosuid,nodev,noexec,relatime - proc proc rw\n"
        "566 564 0:338 / /dev rw,nosuid - tmpfs tmpfs rw,size=65536k,mode=755\n"
        "567 566 0:339 / /dev/pts rw,nosuid,noexec,relatime - devpts devpts rw,gid=5,mode=620,ptmxmode=666\n"
        "568 564 0:161 / /sys ro,nosuid,nodev,noexec,relatime - sysfs sysfs ro\n"
        "569 568 0:30 / /sys/fs/cgroup ro,nosuid,nodev,noexec,relatime - cgroup2 cgroup rw\n"
        "570 566 0:157 / /dev/mqueue rw,nosuid,nodev,noexec,relatime - mqueue mqueue rw\n"
        f"571 566 254:1 /docker/volumes/minikube/_data/lib/kubelet/pods/{K8S_POD_ID}/containers/my-shell/0447d6c5 /dev/termination-log rw,relatime - ext4 /dev/vda1 rw\n"
        "572 564 254:1 /docker/volumes/minikube/_data/lib/docker/containers/bogusPodIdThatShouldNotBeOneSetBecauseTheFirstOneWasPicked\n"
        "573 564 254:1 /docker/volumes/minikube/_data/lib/docker/containers/bogusPodIdThatShouldNotBeOneSetBecauseTheFirstOneWasPicked\n"
        f"574 564 254:1 /docker/volumes/minikube/_data/lib/kubelet/pods/{K8S_POD_ID}/etc-hosts /etc/hosts rw,relatime - ext4 /dev/vda1 rw\n"
        "575 566 0:156 / /bogusPodIdThatShouldNotBeOneSetBecauseTheFirstOneWasPicked\n"
        "576 564 0:153 / /bogusPodIdThatShouldNotBeOneSetBecauseTheFirstOneWasPicked\n"
        "447 566 0:339 /0 /bogusPodIdThatShouldNotBeOneSetBecauseTheFirstOneWasPicked\n"
        "448 565 0:166 /bus /bogusPodIdThatShouldNotBeOneSetBecauseTheFirstOneWasPicked\n"
        "450 565 0:166 /irq /bogusPodIdThatShouldNotBeOneSetBecauseTheFirstOneWasPicked\n"
        "451 565 0:166 /sys /bogusPodIdThatShouldNotBeOneSetBecauseTheFirstOneWasPicked\n"
        "452 565 0:166 /sysrq-trigger /bogusPodIdThatShouldNotBeOneSetBecauseTheFirstOneWasPicked\n"
    )

    with patch("builtins.open", mock_open):
        assert (
            LumigoKubernetesResourceDetector()
            .detect()
            .attributes[ResourceAttributes.K8S_POD_UID]
            == K8S_POD_ID
        )


def test_kubernetes_detector_pod_uid_v2():
    mock_open = MockOpen()
    mock_open["/etc/hosts"].read_data = (
        "# Kubernetes-managed hosts file.\n"
        "127.0.0.1       localhost\n"
        "255.255.255.255 broadcasthost\n"
    )
    mock_open["/proc/self/cgroup"].read_data = (
        f"14:name=systemd:/docker/c24aa3879860ee981d29f0492aef1e39c45d7c7fcdff7bd2050047d0bd390311/kubepods/besteffort/pod{K8S_POD_ID}/bogusPodIdThatShouldNotBeOneSetBecauseTheFirstOneWasPicked\n"
        f"13:rdma:/kubepods/besteffort/pod{K8S_POD_ID}/bogusPodIdThatShouldNotBeOneSetBecauseTheFirstOneWasPicked\n"
        f"12:pids:/docker/c24aa3879860ee981d29f0492aef1e39c45d7c7fcdff7bd2050047d0bd390311/kubepods/besteffort/pod{K8S_POD_ID}/bogusPodIdThatShouldNotBeOneSetBecauseTheFirstOneWasPicked\n"
        f"11:hugetlb:/docker/c24aa3879860ee981d29f0492aef1e39c45d7c7fcdff7bd2050047d0bd390311/kubepods/besteffort/pod{K8S_POD_ID}/bogusPodIdThatShouldNotBeOneSetBecauseTheFirstOneWasPicked\n"
        f"10:net_prio:/docker/c24aa3879860ee981d29f0492aef1e39c45d7c7fcdff7bd2050047d0bd390311/kubepods/besteffort/pod{K8S_POD_ID}/bogusPodIdThatShouldNotBeOneSetBecauseTheFirstOneWasPicked\n"
        f"9:perf_event:/docker/c24aa3879860ee981d29f0492aef1e39c45d7c7fcdff7bd2050047d0bd390311/kubepods/besteffort/pod{K8S_POD_ID}/bogusPodIdThatShouldNotBeOneSetBecauseTheFirstOneWasPicked\n"
        f"8:net_cls:/docker/c24aa3879860ee981d29f0492aef1e39c45d7c7fcdff7bd2050047d0bd390311/kubepods/besteffort/pod{K8S_POD_ID}/bogusPodIdThatShouldNotBeOneSetBecauseTheFirstOneWasPicked\n"
        f"7:freezer:/docker/c24aa3879860ee981d29f0492aef1e39c45d7c7fcdff7bd2050047d0bd390311/kubepods/besteffort/pod{K8S_POD_ID}/bogusPodIdThatShouldNotBeOneSetBecauseTheFirstOneWasPicked\n"
        f"6:devices:/docker/c24aa3879860ee981d29f0492aef1e39c45d7c7fcdff7bd2050047d0bd390311/kubepods/besteffort/pod{K8S_POD_ID}/bogusPodIdThatShouldNotBeOneSetBecauseTheFirstOneWasPicked\n"
        f"5:memory:/docker/c24aa3879860ee981d29f0492aef1e39c45d7c7fcdff7bd2050047d0bd390311/kubepods/besteffort/pod{K8S_POD_ID}/bogusPodIdThatShouldNotBeOneSetBecauseTheFirstOneWasPicked\n"
        f"4:blkio:/docker/c24aa3879860ee981d29f0492aef1e39c45d7c7fcdff7bd2050047d0bd390311/kubepods/besteffort/pod{K8S_POD_ID}/bogusPodIdThatShouldNotBeOneSetBecauseTheFirstOneWasPicked\n"
        f"3:cpuacct:/docker/c24aa3879860ee981d29f0492aef1e39c45d7c7fcdff7bd2050047d0bd390311/kubepods/besteffort/pod{K8S_POD_ID}/bogusPodIdThatShouldNotBeOneSetBecauseTheFirstOneWasPicked\n"
        f"2:cpu:/docker/c24aa3879860ee981d29f0492aef1e39c45d7c7fcdff7bd2050047d0bd390311/kubepods/besteffort/pod{K8S_POD_ID}/bogusPodIdThatShouldNotBeOneSetBecauseTheFirstOneWasPicked\n"
        f"1:cpuset:/docker/c24aa3879860ee981d29f0492aef1e39c45d7c7fcdff7bd2050047d0bd390311/kubepods/besteffort/pod{K8S_POD_ID}/bogusPodIdThatShouldNotBeOneSetBecauseTheFirstOneWasPicked\n"
        f"0::/kubepods/besteffort/pod{K8S_POD_ID}/bogusPodIdThatShouldNotBeOneSetBecauseTheFirstOneWasPicked\n"
    )

    with patch("builtins.open", mock_open):
        assert (
            LumigoKubernetesResourceDetector()
            .detect()
            .attributes[ResourceAttributes.K8S_POD_UID]
            == K8S_POD_ID
        )


def test_lumigo_container_name_detect_not_exist():
    resource = LumigoContainerNameDetector().detect()
    container_name = resource.attributes.get("k8s.container.name")
    assert not container_name


def test_lumigo_container_name_detect(monkeypatch):
    monkeypatch.setenv("LUMIGO_CONTAINER_NAME", "test1234")
    resource = LumigoContainerNameDetector().detect()
    container_name = resource.attributes.get("k8s.container.name")
    assert container_name == "test1234"
