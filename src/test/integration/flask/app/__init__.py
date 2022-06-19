import requests
from flask import Flask
from testcontainers.mongodb import MongoDbContainer
from testcontainers.mysql import MySqlContainer


app = Flask(__name__)


@app.route("/")
def root():
    return {"message": "Hello Flask!"}


@app.get("/invoke-requests")
def invoke_requests():
    response = requests.get("https://api.chucknorris.io/jokes/random")
    return response.json()


@app.get("/invoke-mongo")
def invoke_mongo():
    with MongoDbContainer() as mongo:
        db = mongo.get_connection_client().test
        doc = {
            "address": {
                "street": "2 Avenue",
            },
            "restaurant_id": "41704620",
        }
        db.items.insert_one(doc)
    return {"status": "ok"}


@app.get("/invoke-pymysql")
def invoke_mysql():
    with MySqlContainer():
        return {"status": "ok"}
