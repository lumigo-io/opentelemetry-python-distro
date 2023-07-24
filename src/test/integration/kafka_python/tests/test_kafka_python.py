import json
import time
import unittest
from test.test_utils.spans_parser import SpansContainer

import requests
from testcontainers.kafka import KafkaContainer


class TestFastApiSpans(unittest.TestCase):
    def test_kafka_python_instrumentation(self):
        with KafkaContainer("confluentinc/cp-kafka:latest") as kafka_server:
            response = requests.post(
                "http://localhost:8004/invoke-kafka-producer",
                data=json.dumps(
                    {"bootstrap_servers": kafka_server.get_bootstrap_server()}
                ),
            )

            response.raise_for_status()

            body = response.json()

            self.assertEqual(body, {"status": "ok"})

            response = requests.post(
                "http://localhost:8004/invoke-kafka-consumer",
                data=json.dumps(
                    {"bootstrap_servers": kafka_server.get_bootstrap_server()}
                ),
            )

            response.raise_for_status()

            body = response.json()

            self.assertEqual(body, {"status": "ok"})

            # TODO Do something deterministic
            time.sleep(3)  # Sleep to allow the exporter to catch up

            spans_container = SpansContainer.get_spans_from_file()

            for span in spans_container.spans:
                print(span)

            # TODO this must be updated once the kafka-python instrumentation is implemented
            # without the instrumentation, we should have 8 spans (4 for the producer and 4 for the consumer)
            # that are all related to the http requests to the fastapi server
            assert len(spans_container.spans) == 8
