import os
import sys
import time
import unittest
from testcontainers.redis import RedisContainer
import subprocess

from test.test_utils.spans_parser import SpansContainer


class TestRedisSpans(unittest.TestCase):
    def test_redis_instrumentation(self):
        with RedisContainer("redis:latest") as redis_server:
            example_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "../app/redis_set_and_get.py",
            )
            subprocess.check_output(
                [sys.executable, example_path],
                env={
                    **os.environ,
                    "REDIS_HOST": redis_server.get_container_host_ip(),
                    "REDIS_PORT": str(redis_server.get_exposed_port(6379)),
                    "AUTOWRAPT_BOOTSTRAP": "lumigo_opentelemetry",
                    "OTEL_SERVICE_NAME": "app",
                },
            )
            # TODO Do something deterministic
            time.sleep(3)  # Sleep to allow the exporter to catch up
            spans_container = SpansContainer.parse_spans_from_file()

            self.assertGreaterEqual(len(spans_container.spans), 2)
            set_span, get_span = spans_container.spans
            self.assertEqual(set_span["attributes"]["db.system"], "redis")
            self.assertEqual(
                set_span["attributes"]["redis.request.args"],
                '["SET", "my-key", "my-value"]',
            )
            self.assertEqual(set_span["attributes"]["redis.request.kwargs"], "{}")
            self.assertEqual(set_span["attributes"]["redis.response.body"], "True")

            self.assertEqual(get_span["attributes"]["db.system"], "redis")
            self.assertEqual(
                get_span["attributes"]["redis.request.args"], '["GET", "my-key"]'
            )
            self.assertEqual(get_span["attributes"]["redis.request.kwargs"], "{}")
            self.assertEqual(get_span["attributes"]["redis.response.body"], "my-value")
