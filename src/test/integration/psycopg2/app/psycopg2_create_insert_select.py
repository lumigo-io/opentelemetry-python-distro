import os
from urllib.parse import urlparse

import psycopg2

CONNECTION_URL = os.environ["CONNECTION_URL"]
TEST_NAME = os.environ["TEST_NAME"]
TEST_EMAIL = os.environ["TEST_EMAIL"]

parsed_connection = urlparse(CONNECTION_URL)
connection = psycopg2.connect(
    database=parsed_connection.path[1:],
    user=parsed_connection.username,
    password=parsed_connection.password,
    host=parsed_connection.hostname,
    port=parsed_connection.port,
)

cursor = connection.cursor()
cursor.execute("SELECT VERSION()")
cursor.execute(
    "CREATE TABLE users (id SERIAL PRIMARY KEY, name VARCHAR(255), email VARCHAR(255))"
)
cursor.execute("INSERT INTO users (name, email) VALUES (%s, %s)", (TEST_NAME, TEST_EMAIL))
cursor.execute("SELECT * FROM users")
result = cursor.fetchall()
connection.commit()
cursor.close()
connection.close()
