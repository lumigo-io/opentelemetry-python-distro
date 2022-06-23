import requests
from flask import Flask


app = Flask(__name__)


@app.route("/")
def root():
    return {"message": "Hello Flask!"}


@app.get("/invoke-requests")
def invoke_requests():
    response = requests.get("https://api.chucknorris.io/jokes/random")
    return response.json()
