import requests
from fastapi import FastAPI
from opentelemetry.trace import get_current_span


app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello FastAPI!"}


@app.get("/invoke-request")
def invoke_request():
    response = requests.get("https://api.chucknorris.io/jokes/random")
    get_current_span().set_attribute("big_response_len", len(response.text))
    get_current_span().set_attribute(
        "lumigo.execution_tags.response_len", len(response.text)
    )
    get_current_span().set_attribute("lumigo.execution_tags.response", response.text)
    get_current_span().set_attribute("lumigo.execution_tags.app", True)
    get_current_span().set_attribute("lumigo.execution_tags.app.response", "success")
    get_current_span().set_attribute("lumigo.execution_tags.foo", ("bar", "baz"))
    return response.json()


@app.get("/invoke-requests-large-response")
def invoke_requests_big_response():
    response = requests.get("http://localhost:8021/big-response")
    return response.json()
