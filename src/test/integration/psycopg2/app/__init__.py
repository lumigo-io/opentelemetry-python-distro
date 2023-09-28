from urllib.parse import urlparse

import psycopg2
from fastapi import FastAPI

app = FastAPI()

connection_url = None


def get_connection():
    global connection_url
    if connection_url is None:
        raise Exception("Connection URL is not initialized")
    parsed_connection = urlparse(connection_url)
    return psycopg2.connect(
        database=parsed_connection.path[1:],
        user=parsed_connection.username,
        password=parsed_connection.password,
        host=parsed_connection.hostname,
        port=parsed_connection.port,
    )


@app.get("/")
async def root():
    return {"message": "Hello FastAPI!"}


@app.post("/init")
def init(props: dict):
    global connection_url
    connection_url = props["connection_url"]
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT VERSION()")
    cursor.execute(
        "CREATE TABLE users (id SERIAL PRIMARY KEY, name VARCHAR(255), email VARCHAR(255))"
    )
    connection.commit()
    cursor.close()
    connection.close()
    return {"status": "ok"}


@app.post("/add-user")
def add_user(req_body: dict):
    name = req_body["name"]
    email = req_body["email"]
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("INSERT INTO users (name, email) VALUES (%s, %s)", (name, email))
    connection.commit()
    cursor.close()
    connection.close()
    return {"status": "ok"}


@app.get("/users")
def get_users():
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM users")
    result = cursor.fetchall()
    cursor.close()
    connection.close()
    return {"users": result}
