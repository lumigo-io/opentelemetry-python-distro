import json
import os
import requests
import responses
import lumigo_opentelemetry.resources.detectors as detectors

from unittest.mock import patch, MagicMock

_AWS_ECS_METADATA_URL='http://test.uri.ecs'

def load_json(filename):
    with open(os.path.join(os.path.dirname(__file__), filename)) as file:
        return json.loads(file.read())
    

_metadata_container_response = load_json('metadatav4-response-container.json')
_metadata_task_response = load_json('metadatav4-response-task.json')


@responses.activate
def test_happy_path():
    responses.add(
        method="GET",
        url=_AWS_ECS_METADATA_URL,
        json=_metadata_container_response
    )

    responses.add(
        method="GET",
        url=f"{_AWS_ECS_METADATA_URL}/task",
        json=_metadata_task_response
    )

    with patch.dict(os.environ, {"ECS_CONTAINER_METADATA_URI_V4": _AWS_ECS_METADATA_URL}):
        resource = detectors.AwsEcsResourceDetector().detect()

    assert resource.attributes['aws.ecs.container.arn'] == 'arn:aws:ecs:us-west-2:111122223333:container/0206b271-b33f-47ab-86c6-a0ba208a70a9'
    assert resource.attributes['aws.ecs.cluster.arn'] == 'arn:aws:ecs:us-west-2:111122223333:cluster/default'
    assert resource.attributes['aws.ecs.launchtype'] == 'EC2'
    assert resource.attributes['aws.ecs.task.arn'] == 'arn:aws:ecs:us-west-2:111122223333:task/default/158d1c8083dd49d6b527399fd6414f5c'
    assert resource.attributes['aws.ecs.task.family'] == 'curltest'
    assert resource.attributes['aws.ecs.task.revision'] == '26'

def test_timeout():
    timeout_error = requests.exceptions.Timeout()

    with patch.object(detectors._aws_ecs_detector_logger, 'error', MagicMock()):
        with patch.object(requests, 'get', side_effect=timeout_error):
            with patch.dict(os.environ, {'ECS_CONTAINER_METADATA_URI_V4': _AWS_ECS_METADATA_URL}):
                resource = detectors.AwsEcsResourceDetector().detect()

                assert not resource.attributes
                detectors._aws_ecs_detector_logger.error.assert_called_once_with("An error occurred while looking up the AWS ECS resource attributes: %s", timeout_error)

def test_no_ecs():
    assert not detectors.AwsEcsResourceDetector().detect().attributes
