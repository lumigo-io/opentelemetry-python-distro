from opentelemetry.semconv.resource import (
    ResourceAttributes,
    CloudProviderValues,
    CloudPlatformValues,
)

MockEksResourceAttributes = {
    ResourceAttributes.CLOUD_PROVIDER: CloudProviderValues.AWS.value,
    ResourceAttributes.CLOUD_PLATFORM: CloudPlatformValues.AWS_EKS.value,
    ResourceAttributes.K8S_CLUSTER_NAME: "mock-cluster-name",
    ResourceAttributes.CONTAINER_ID: "a4d00c9dd675d67f866c786181419e1b44832d4696780152e61afd44a3e02856",
}


get_cluster_info = f"""{{
  "kind": "ConfigMap",
  "apiVersion": "v1",
  "metadata": {{
    "name": "cluster-info",
    "namespace": "amazon-cloudwatch",
    "selfLink": "/api/v1/namespaces/amazon-cloudwatch/configmaps/cluster-info",
    "uid": "0734438c-48f4-45c3-b06d-b6f16f7f0e1e",
    "resourceVersion": "25911",
    "creationTimestamp": "2021-07-23T18:41:56Z",
    "annotations": {{
      "kubectl.kubernetes.io/last-applied-configuration": "{{\\"apiVersion\\":\\"v1\\",\\"data\\":{{\\"cluster.name\\":\\"{MockEksResourceAttributes[ResourceAttributes.K8S_CLUSTER_NAME]}\\",\\"logs.region\\":\\"us-west-2\\"}},\\"kind\\":\\"ConfigMap\\",\\"metadata\\":{{\\"annotations\\":{{}},\\"name\\":\\"cluster-info\\",\\"namespace\\":\\"amazon-cloudwatch\\"}}}}\\n"
    }}
  }},
  "data": {{
    "cluster.name": "{MockEksResourceAttributes[ResourceAttributes.K8S_CLUSTER_NAME]}",
    "logs.region": "us-west-2"
  }}
}}
"""

container_id_text = f"""14:name=systemd:/docker/{MockEksResourceAttributes[ResourceAttributes.CONTAINER_ID]}
13:rdma:/
12:pids:/docker/bogusContainerIdThatShouldNotBeOneSetBecauseTheFirstOneWasPicked
11:hugetlb:/docker/bogusContainerIdThatShouldNotBeOneSetBecauseTheFirstOneWasPicked
10:net_prio:/docker/bogusContainerIdThatShouldNotBeOneSetBecauseTheFirstOneWasPicked
9:perf_event:/docker/bogusContainerIdThatShouldNotBeOneSetBecauseTheFirstOneWasPicked
8:net_cls:/docker/bogusContainerIdThatShouldNotBeOneSetBecauseTheFirstOneWasPicked
7:freezer:/docker/
6:devices:/docker/bogusContainerIdThatShouldNotBeOneSetBecauseTheFirstOneWasPicked
5:memory:/docker/bogusContainerIdThatShouldNotBeOneSetBecauseTheFirstOneWasPicked
4:blkio:/docker/bogusContainerIdThatShouldNotBeOneSetBecauseTheFirstOneWasPicked
3:cpuacct:/docker/bogusContainerIdThatShouldNotBeOneSetBecauseTheFirstOneWasPicked
2:cpu:/docker/bogusContainerIdThatShouldNotBeOneSetBecauseTheFirstOneWasPicked
1:cpuset:/docker/bogusContainerIdThatShouldNotBeOneSetBecauseTheFirstOneWasPicked
"""
