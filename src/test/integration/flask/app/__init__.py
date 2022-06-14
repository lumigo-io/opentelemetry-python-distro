import requests
from flask import Flask
import boto3
from botocore import UNSIGNED
from botocore.client import Config
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


@app.post("/invoke-boto3")
def invoke_boto3():
    s3 = boto3.client("s3", config=Config(signature_version=UNSIGNED))
    # raises (AccessDenied)
    try:
        s3.list_objects(Bucket="sentinel-s2-l1c")
    except Exception:
        return {"status": "ok"}


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
