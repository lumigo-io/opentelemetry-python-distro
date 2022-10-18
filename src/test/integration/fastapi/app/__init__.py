from time import sleep

import requests
from fastapi import FastAPI
from requests import HTTPError

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello FastAPI!"}


@app.get("/invoke-requests")
def invoke_requests():
    response = requests.get("https://api.chucknorris.io/jokes/random")
    return response.json()


@app.get("/invoke-requests-large-response")
def invoke_requests_big_response():
    for _ in range(10):
        try:
            r = requests.get("https://api.publicapis.org/health")
            r.raise_for_status()
            break
        except HTTPError as e:
            print(e.response)
            print("got exception, retrying")
            sleep(2)

    response = requests.get("https://api.publicapis.org/entries")
    response.raise_for_status()
    return response.json()
