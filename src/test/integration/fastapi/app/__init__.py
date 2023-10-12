import requests
from fastapi import FastAPI

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello FastAPI!"}


@app.get("/invoke-requests")
def invoke_requests():
    response = requests.get("http://localhost:8021/little-response")
    return response.json()


@app.get("/invoke-requests-large-response")
def invoke_requests_big_response():
    response = requests.get("http://localhost:8021/big-response")
    response.raise_for_status()
    return response.json()


print("FastAPI app started")
