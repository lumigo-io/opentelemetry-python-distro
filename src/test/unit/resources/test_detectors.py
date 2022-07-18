from opentelemetry.sdk import resources

from lumigo_opentelemetry.resources.detectors import ProcessResourceDetector


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
