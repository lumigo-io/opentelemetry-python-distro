import requests
from fastapi import FastAPI


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
    response = requests.get("https://api.publicapis.org/entries")
    return response.json()
