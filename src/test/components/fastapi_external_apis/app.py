from fastapi import FastAPI

app = FastAPI()


@app.get("/big-response")
def get_big_response():
    return {"data": "a" * 10_000}
