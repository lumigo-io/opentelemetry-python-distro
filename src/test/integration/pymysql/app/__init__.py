from fastapi import FastAPI
from testcontainers.mysql import MySqlContainer

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello FastAPI!"}


@app.get("/invoke-pymysql")
def invoke_mysql():
    with MySqlContainer():
        return {"status": "ok"}
