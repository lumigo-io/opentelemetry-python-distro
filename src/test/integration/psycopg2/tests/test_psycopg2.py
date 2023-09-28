import unittest
from test.test_utils.span_exporter import wait_for_exporter
from test.test_utils.spans_parser import SpansContainer

import requests
from testcontainers.postgres import PostgresContainer

APP_HOST = "http://localhost:8006"


class TestPsycopg2Spans(unittest.TestCase):
    def test_psycopg2_instrumentation(self):
        with PostgresContainer("postgres:latest") as postgres:
            response = requests.post(
                f"{APP_HOST}/init",
                json={"connection_url": postgres.get_connection_url()},
            )
            response.raise_for_status()

            body = response.json()
            self.assertEqual(body, {"status": "ok"})

            response = requests.post(
                f"{APP_HOST}/add-user", json={"name": "Bob", "email": "bob@psycopg.to"}
            )
            response.raise_for_status()

            body = response.json()
            self.assertEqual(body, {"status": "ok"})

            response = requests.get(f"{APP_HOST}/users")
            response.raise_for_status()

            body = response.json()
            self.assertTrue("users" in body)

            wait_for_exporter()

            spans_container = SpansContainer.get_spans_from_file()

            root_spans = spans_container.get_root_spans()
            self.assertEqual(len(root_spans), 3)

            init_trace_span_root = root_spans[0]

            select_spans = spans_container.get_non_internal_children(
                name_filter="SELECT", root_span=init_trace_span_root
            )
            self.assertEqual(len(select_spans), 1)
            self.assertEqual(select_spans[0]["attributes"]["db.system"], "postgresql")
            self.assertEqual(
                select_spans[0]["attributes"]["db.statement"], "SELECT VERSION()"
            )

            create_table_spans = spans_container.get_non_internal_children(
                name_filter="CREATE", root_span=init_trace_span_root
            )
            self.assertEqual(len(create_table_spans), 1)
            self.assertEqual(
                create_table_spans[0]["attributes"]["db.system"], "postgresql"
            )
            self.assertTrue(
                create_table_spans[0]["attributes"]["db.statement"].startswith(
                    "CREATE TABLE users"
                )
            )

            add_user_trace_span_root = root_spans[1]

            add_user_spans = spans_container.get_non_internal_children(
                name_filter="INSERT", root_span=add_user_trace_span_root
            )
            self.assertEqual(len(add_user_spans), 1)
            self.assertEqual(add_user_spans[0]["attributes"]["db.system"], "postgresql")
            self.assertTrue(
                add_user_spans[0]["attributes"]["db.statement"].startswith(
                    "INSERT INTO users"
                )
            )

            get_users_trace_span_root = root_spans[2]

            get_users_spans = spans_container.get_non_internal_children(
                name_filter="SELECT", root_span=get_users_trace_span_root
            )
            self.assertEqual(len(get_users_spans), 1)
            self.assertEqual(
                get_users_spans[0]["attributes"]["db.system"], "postgresql"
            )
            self.assertEqual(
                get_users_spans[0]["attributes"]["db.statement"], "SELECT * FROM users"
            )
