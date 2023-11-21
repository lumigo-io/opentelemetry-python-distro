import os
from urllib.parse import urlparse

CONNECTION_URL = os.environ["CONNECTION_URL"]
TEST_NAME = os.environ["TEST_NAME"]
TEST_EMAIL = os.environ["TEST_EMAIL"]

parsed_connection = urlparse(CONNECTION_URL)

if os.environ["MODULE_UNDER_TESTING"] == "psycopg2":
    import psycopg2 as psycopg

    connection = psycopg.connect(
        database=parsed_connection.path[1:],
        user=parsed_connection.username,
        password=parsed_connection.password,
        host=parsed_connection.hostname,
        port=parsed_connection.port,
    )
elif os.environ["MODULE_UNDER_TESTING"] == "psycopg":
    import psycopg

    connection = psycopg.connect(
        dbname=parsed_connection.path[1:],
        user=parsed_connection.username,
        password=parsed_connection.password,
        host=parsed_connection.hostname,
        port=parsed_connection.port,
    )
else:
    raise Exception("Invalid module under testing")


cursor = connection.cursor()
cursor.execute("SELECT VERSION()")
cursor.execute(
    "CREATE TABLE users (id SERIAL PRIMARY KEY, name VARCHAR(255), email VARCHAR(255))"
)
cursor.execute(
    "INSERT INTO users (name, email) VALUES (%s, %s)", (TEST_NAME, TEST_EMAIL)
)

connection.commit()

cursor.execute("SELECT * FROM users")
result = cursor.fetchall()

cursor.close()
connection.close()
