import requests
from fastapi import FastAPI


app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello FastAPI!"}


@app.get("/invoke-requests-large-response")
def invoke_requests_big_response():
    response = requests.get("https://api.publicapis.org/entries")
    return response.json()
