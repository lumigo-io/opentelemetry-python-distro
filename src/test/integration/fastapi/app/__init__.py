from fastapi import FastAPI
import requests

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello FastAPI!"}


@app.get("/unmatched")
async def unmatched():
    return {"message": "Hello again, FastAPI!"}


@app.post("/invoke-requests")
def invoke_requests(request: dict):
    return {"url": "http://sheker.kol.shehoo:8021/little-response", "data": "a" * 100}


@app.get("/call-external")
def call_external():
    response = requests.get("http://example.com")
    return {"status_code": response.status_code}


@app.get("/invoke-requests-large-response")
def invoke_requests_big_response():
    return {"data": "a" * 10_000}


print("FastAPI app started")
