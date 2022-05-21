from fastapi import FastAPI, HTTPException
from starlette.exceptions import HTTPException as StarletteHTTPException

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello FastAPI!"}

@app.get("/accounts/{account_id}")
async def account(account_id):
    if account_id == "taz":
        raise HTTPException(status_code=400, detail="400 response")

    if account_id == "blitz":
        raise HTTPException(status_code=404, detail="404 response")

    if account_id == "alcatraz_smedry":
        raise HTTPException(status_code=500, detail="500 response")

    if account_id == "kaboom":
        raise StarletteHTTPException(status_code=500, detail="500 response")

    return {"account": account_id}
