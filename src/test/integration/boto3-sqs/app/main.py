import boto3

from lumigo_opentelemetry import tracer_provider
from opentelemetry.trace import SpanKind

from moto import mock_sqs


@mock_sqs
def run():
    tracer = tracer_provider.get_tracer(__name__)

    client = boto3.client("sqs", region_name="eu-central-1")
    queue = client.create_queue(QueueName="test")

    # Simulate polling an empty sqs queue
    client.receive_message(QueueUrl=queue["QueueUrl"], MaxNumberOfMessages=1)
    client.receive_message(QueueUrl=queue["QueueUrl"], MaxNumberOfMessages=1)
    client.receive_message(QueueUrl=queue["QueueUrl"], MaxNumberOfMessages=1)

    client.send_message(
        QueueUrl=queue["QueueUrl"],
        MessageBody="Message_1",
    )
    client.send_message(
        QueueUrl=queue["QueueUrl"],
        MessageBody="Message_2",
    )

    messages_copy = None

    response = client.receive_message(QueueUrl=queue["QueueUrl"], MaxNumberOfMessages=1)

    if response:
        if "Messages" in response and response["Messages"]:
            for message in response["Messages"]:
                # In the iterator, we restore the span for client.receive_message
                with tracer.start_as_current_span(
                    "consuming_message_1", kind=SpanKind.INTERNAL
                ) as processing_span:
                    processing_span.set_attribute("message.body", message["Body"])

                    with tracer.start_as_current_span(
                        "consuming_message_2", kind=SpanKind.INTERNAL
                    ) as processing_span:
                        processing_span.set_attribute("foo", "bar")

            messages_copy = response["Messages"].copy()

    for message in messages_copy:
        with tracer.start_as_current_span(
            "iterator_on_copy", kind=SpanKind.INTERNAL
        ) as span:
            span.set_attribute("foo", "bar")

    response = client.receive_message(QueueUrl=queue["QueueUrl"], MaxNumberOfMessages=1)
    if response:
        for message in response["Messages"]:
            # In the iterator, we must restore the span for client.receive_message
            break  # Here we are supposed to lose the trace context

    with tracer.start_as_current_span(
        "after_iterator_break", kind=SpanKind.INTERNAL
    ) as span:
        span.set_attribute("foo", "bar")

    tracer_provider.force_flush()


if __name__ == "__main__":
    run()
