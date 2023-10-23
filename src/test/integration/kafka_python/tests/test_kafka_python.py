import json
import unittest
from test.test_utils.span_exporter import wait_for_exporter
from test.test_utils.spans_parser import SpansContainer

import requests
from testcontainers.kafka import KafkaContainer


class TestKafkaSpans(unittest.TestCase):
    def test_kafka_python_instrumentation(self):
        test_topic = "kafka-python-topic"
        with KafkaContainer("confluentinc/cp-kafka:latest") as kafka_server:
            response = requests.post(
                "http://localhost:8004/invoke-kafka-producer",
                data=json.dumps(
                    {
                        "bootstrap_servers": kafka_server.get_bootstrap_server(),
                        "topic": test_topic,
                    }
                ),
            )

            response.raise_for_status()

            body = response.json()

            self.assertEqual(body, {"status": "ok"})

            response = requests.post(
                "http://localhost:8004/invoke-kafka-consumer",
                data=json.dumps(
                    {
                        "bootstrap_servers": kafka_server.get_bootstrap_server(),
                        "topic": test_topic,
                    }
                ),
            )

            response.raise_for_status()

            body = response.json()

            self.assertEqual(body, {"status": "ok"})

            wait_for_exporter()

            spans_container = SpansContainer.get_spans_from_file()

            assert len(spans_container.spans) > 10

            for span in spans_container.spans:
                if span["name"].startswith(test_topic):
                    if span["name"].endswith("send"):
                        send_span = span
                    if span["name"].endswith("receive"):
                        receive_span = span

            # assert kafka spans
            assert send_span["kind"] == "SpanKind.PRODUCER"
            assert send_span["attributes"]["messaging.system"] == "kafka"
            assert send_span["attributes"]["messaging.destination"] == test_topic
            assert send_span["attributes"]["messaging.produce.body"] == "{'foo': 'bar'}"

            assert receive_span
            assert receive_span["kind"] == "SpanKind.CONSUMER"
            assert receive_span["attributes"]["messaging.system"] == "kafka"
            assert receive_span["attributes"]["messaging.destination"] == test_topic
            assert (
                receive_span["attributes"]["messaging.consume.body"] == "{'foo': 'bar'}"
            )

            assert (
                send_span["attributes"]["messaging.kafka.partition"]
                == receive_span["attributes"]["messaging.kafka.partition"]
            )
            assert (
                send_span["attributes"]["messaging.url"]
                == receive_span["attributes"]["messaging.url"]
            )
