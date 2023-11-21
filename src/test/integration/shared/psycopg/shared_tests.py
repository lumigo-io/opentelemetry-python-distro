import os
import random
import string
import unittest
from test.integration.shared.psycopg.utils import run_psycopg_sample
from test.test_utils.span_exporter import wait_for_exporter
from test.test_utils.spans_parser import SpansContainer

from testcontainers.postgres import PostgresContainer


def random_string(length: int) -> str:
    return "".join(random.choice(string.ascii_lowercase) for _ in range(length))


def generate_test_data():
    test_name = random_string(10)
    test_email = f"{test_name}@{random_string(10)}.{random_string(3)}"
    return test_name, test_email


class TestPsycopgSpans(unittest.TestCase):
    def test_psycopg_create_add_select(self):
        with PostgresContainer("postgres:latest") as postgres:
            test_name, test_email = generate_test_data()
            run_psycopg_sample(
                "create_insert_select",
                connection_url=postgres.get_connection_url(),
                test_name=test_name,
                test_email=test_email,
                module_under_testing=os.environ["MODULE_UNDER_TESTING"],
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
