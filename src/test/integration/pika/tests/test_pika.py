import json
import time
import unittest
from test.test_utils.spans_parser import SpansContainer

import requests
from testcontainers.rabbitmq import RabbitMqContainer


class TestFastApiSpans(unittest.TestCase):
    def test_pika_instrumentation(self):
        test_topic = "test-pika-topic"
        with RabbitMqContainer("rabbitmq:latest") as rabbitmq_server:
            connection_params = {
                "host": rabbitmq_server.get_container_host_ip(),
                "port": rabbitmq_server.get_exposed_port(5672),
            }

            response = requests.post(
                "http://localhost:8005/invoke-pika-producer",
                data=json.dumps(
                    {
                        "connection_params": connection_params,
                        "topic": test_topic,
                    }
                ),
            )

            response.raise_for_status()

            body = response.json()

            self.assertEqual(body, {"status": "ok"})

            response = requests.post(
                "http://localhost:8005/invoke-pika-consumer",
                data=json.dumps(
                    {
                        "connection_params": connection_params,
                        "topic": test_topic,
                    }
                ),
            )

            response.raise_for_status()

            body = response.json()

            self.assertEqual(body, {"status": "ok"})

            # TODO Do something deterministic
            time.sleep(3)  # Sleep to allow the exporter to catch up

            spans_container = SpansContainer.get_spans_from_file()

            assert len(spans_container.spans) == 10

            for span in spans_container.spans:
                if span["name"].startswith(test_topic):
                    if span["name"].endswith("send"):
                        send_span = span
                    if span["name"].endswith("receive"):
                        receive_span = span

            # assert pika spans
            assert send_span["kind"] == "SpanKind.PRODUCER"
            assert send_span["attributes"]["messaging.system"] == "rabbitmq"
            assert send_span["attributes"]["net.peer.name"] == "localhost"
            assert send_span["attributes"]["messaging.publish.body"] == "Hello World!"

            assert receive_span
            assert receive_span["kind"] == "SpanKind.CONSUMER"
            assert receive_span["attributes"]["messaging.system"] == "rabbitmq"
            assert receive_span["attributes"]["net.peer.name"] == "localhost"
            assert (
                receive_span["attributes"]["messaging.consume.body"] == "Hello World!"
            )

            assert (
                send_span["attributes"]["net.peer.port"]
                == receive_span["attributes"]["net.peer.port"]
            )
