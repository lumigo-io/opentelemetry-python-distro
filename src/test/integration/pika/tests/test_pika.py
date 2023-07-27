import json
import time
import unittest
from test.test_utils.spans_parser import SpansContainer

import requests
from testcontainers.rabbitmq import RabbitMqContainer


class TestFastApiSpans(unittest.TestCase):
    def test_pika_instrumentation(self):
        with RabbitMqContainer("rabbitmq:latest") as rabbitmq_server:
            connection_params = {
                "host": rabbitmq_server.get_container_host_ip(),
                "port": rabbitmq_server.get_exposed_port(5672),
            }

            response = requests.post(
                "http://localhost:8005/invoke-pika-producer",
                data=json.dumps(connection_params),
            )

            response.raise_for_status()

            body = response.json()

            self.assertEqual(body, {"status": "ok"})

            response = requests.post(
                "http://localhost:8005/invoke-pika-consumer",
                data=json.dumps(connection_params),
            )

            response.raise_for_status()

            body = response.json()

            self.assertEqual(body, {"status": "ok"})

            # TODO Do something deterministic
            time.sleep(3)  # Sleep to allow the exporter to catch up

            spans_container = SpansContainer.get_spans_from_file()

            for span in spans_container.spans:
                print(span)

            # TODO this must be updated once the pika instrumentation is implemented
            # without the instrumentation, we should have 8 spans (4 for the producer and 4 for the consumer)
            # that are all related to the http requests to the fastapi server
            assert len(spans_container.spans) == 8
