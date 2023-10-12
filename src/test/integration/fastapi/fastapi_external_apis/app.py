from fastapi import FastAPI, Request

app = FastAPI()


@app.get("/big-response")
def get_big_response():
    return {"data": "a" * 10_000}


@app.get("/little-response")
def get_little_response(request: Request):
    return {
        "url": str(request.url),
        "data": "a" * 100
    }
