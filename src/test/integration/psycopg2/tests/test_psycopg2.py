import os
import subprocess
import sys
import unittest
from os import path
from test.test_utils.span_exporter import wait_for_exporter
from test.test_utils.spans_parser import SpansContainer

from testcontainers.postgres import PostgresContainer

APP_HOST = "http://localhost:8006"


def run_psycopg2_sample(
    sample_name: str, connection_url: str, test_name: str, test_email: str
):
    sample_path = path.join(
        path.dirname(path.abspath(__file__)),
        f"../app/psycopg2_{sample_name}.py",
    )
    subprocess.check_output(
        [sys.executable, sample_path],
        env={
            **os.environ,
            "CONNECTION_URL": connection_url,
            "TEST_NAME": test_name,
            "TEST_EMAIL": test_email,
            "AUTOWRAPT_BOOTSTRAP": "lumigo_opentelemetry",
            "OTEL_SERVICE_NAME": f"psycopg2_{sample_name}-app",
        },
    )


class TestPsycopg2Spans(unittest.TestCase):
    def test_psycopg2_create_add_select(self):
        with PostgresContainer("postgres:latest") as postgres:
            test_name = "Bob"
            test_email = "bob@psycopg.to"
            run_psycopg2_sample(
                "create_insert_select",
                connection_url=postgres.get_connection_url(),
                test_name=test_name,
                test_email=test_email,
            )

            wait_for_exporter()

            spans_container = SpansContainer.get_spans_from_file()

            root_spans = spans_container.get_root_spans()
            self.assertEqual(len(root_spans), 5, "There should be 5 root spans")

            select_version_span = root_spans[0]

            self.assertEqual(
                select_version_span["attributes"]["db.system"], "postgresql"
            )
            self.assertEqual(
                select_version_span["attributes"]["db.statement"], "SELECT VERSION()"
            )

            create_table_span = root_spans[1]

            self.assertEqual(create_table_span["attributes"]["db.system"], "postgresql")
            self.assertTrue(
                create_table_span["attributes"]["db.statement"].startswith(
                    "CREATE TABLE users"
                )
            )

            insert_user_span = root_spans[2]

            self.assertEqual(insert_user_span["attributes"]["db.system"], "postgresql")
            self.assertTrue(
                insert_user_span["attributes"]["db.statement"].startswith(
                    "INSERT INTO users"
                )
            )
            self.assertIn(
                f"('{test_name}', '{test_email}')",
                insert_user_span["attributes"]["db.statement.parameters"],
            )

            select_users_span = root_spans[3]

            self.assertEqual(select_users_span["attributes"]["db.system"], "postgresql")
            self.assertEqual(
                select_users_span["attributes"]["db.statement"], "SELECT * FROM users"
            )

            fetch_all_span = root_spans[4]

            self.assertEqual(fetch_all_span["attributes"]["db.system"], "postgresql")
            self.assertIn(
                f'[[1, "{test_name}", "{test_email}"]]',
                fetch_all_span["attributes"]["db.response.body"],
            )
