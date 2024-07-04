import ast
import os
import subprocess
import sys
import unittest
from os import path
from test.test_utils.span_exporter import wait_for_exporter
from test.test_utils.spans_parser import SpansContainer

from testcontainers.redis import RedisContainer

ATTRIBUTES = "attributes"
DB_STATEMENT = "db.statement"
DB_SYSTEM = "db.system"
REDIS_RESPONSE_BODY = "db.response.body"


def run_redis_sample(sample_name: str, redis_host: str, redis_port: int):
    sample_path = path.join(
        path.dirname(path.abspath(__file__)),
        f"../app/redis_{sample_name}.py",
    )
    subprocess.check_output(
        [sys.executable, sample_path],
        env={
            **os.environ,
            "REDIS_HOST": redis_host,
            "REDIS_PORT": str(redis_port),
            "AUTOWRAPT_BOOTSTRAP": "lumigo_opentelemetry",
            "OTEL_SERVICE_NAME": f"redis_{sample_name}-app",
        },
    )


class TestRedisSpans(unittest.TestCase):
    def test_redis_set_and_get(self):
        with RedisContainer("redis:latest") as redis_server:
            run_redis_sample(
                "set_and_get",
                redis_server.get_container_host_ip(),
                redis_server.get_exposed_port(6379),
            )

            wait_for_exporter()

            spans_container = SpansContainer.parse_spans_from_file()

            self.assertGreaterEqual(len(spans_container.spans), 4)
            set_span, get_span, set_bytes_span, get_bytes_span = spans_container.spans
            self.assertEqual(set_span[ATTRIBUTES][DB_SYSTEM], "redis")
            self.assertEqual(
                set_span[ATTRIBUTES][DB_STATEMENT],
                "SET my-key my-value",
            )
            self.assertEqual(set_span[ATTRIBUTES][REDIS_RESPONSE_BODY], "True")

            self.assertEqual(get_span[ATTRIBUTES][DB_SYSTEM], "redis")
            self.assertEqual(get_span[ATTRIBUTES][DB_STATEMENT], "GET my-key")
            self.assertEqual(get_span[ATTRIBUTES][REDIS_RESPONSE_BODY], "my-value")

            self.assertEqual(set_bytes_span[ATTRIBUTES][DB_SYSTEM], "redis")
            self.assertEqual(
                set_bytes_span[ATTRIBUTES][DB_STATEMENT],
                "SET my-bytes-key b'my-bytes-value'",
            )
            self.assertEqual(set_bytes_span[ATTRIBUTES][REDIS_RESPONSE_BODY], "True")

            self.assertEqual(get_bytes_span[ATTRIBUTES][DB_SYSTEM], "redis")
            self.assertEqual(
                get_bytes_span[ATTRIBUTES][DB_STATEMENT], "GET my-bytes-key"
            )
            self.assertEqual(
                get_bytes_span[ATTRIBUTES][REDIS_RESPONSE_BODY], "my-bytes-value"
            )

    def test_redis_hash(self):
        with RedisContainer("redis:latest") as redis_server:
            run_redis_sample(
                "hash",
                redis_server.get_container_host_ip(),
                redis_server.get_exposed_port(6379),
            )

            wait_for_exporter()

            spans_container = SpansContainer.parse_spans_from_file()

            self.assertGreaterEqual(len(spans_container.spans), 2)
            set_span, get_span = spans_container.spans
            self.assertEqual(set_span[ATTRIBUTES][DB_SYSTEM], "redis")
            self.assertEqual(
                set_span[ATTRIBUTES][DB_STATEMENT],
                "HMSET my-key key1 value1 key2 value2",
            )
            self.assertEqual(set_span[ATTRIBUTES][REDIS_RESPONSE_BODY], "True")

            self.assertEqual(get_span[ATTRIBUTES][DB_SYSTEM], "redis")
            self.assertEqual(get_span[ATTRIBUTES][DB_STATEMENT], "HGETALL my-key")
            self.assertEqual(
                ast.literal_eval(get_span[ATTRIBUTES][REDIS_RESPONSE_BODY]),
                {b"key1": b"value1", b"key2": b"value2"},
            )

    def test_redis_transaction(self):
        with RedisContainer("redis:latest") as redis_server:
            run_redis_sample(
                "transaction",
                redis_server.get_container_host_ip(),
                redis_server.get_exposed_port(6379),
            )

            wait_for_exporter()

            spans_container = SpansContainer.parse_spans_from_file()

            self.assertGreaterEqual(len(spans_container.spans), 1)
            transaction_span = spans_container.spans[0]
            self.assertEqual(transaction_span[ATTRIBUTES][DB_SYSTEM], "redis")
            self.assertEqual(
                transaction_span[ATTRIBUTES][DB_STATEMENT].split("\n"),
                [
                    "SET ? ?",
                    "GET ?",
                    "SET ? ?",
                    "GET ?",
                    "GET ?",
                ],
            )
            self.assertEqual(
                ast.literal_eval(transaction_span[ATTRIBUTES][REDIS_RESPONSE_BODY]),
                [True, b"pre-key-value", True, b"key-value", None],
            )
