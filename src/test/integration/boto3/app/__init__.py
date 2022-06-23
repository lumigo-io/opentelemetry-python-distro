from fastapi import FastAPI
import boto3
from botocore import UNSIGNED
from botocore.client import Config


app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello FastAPI!"}


@app.post("/invoke-boto3")
def invoke_boto3():
    s3 = boto3.client("s3", config=Config(signature_version=UNSIGNED))
    # raises (AccessDenied)
    try:
        s3.list_objects(Bucket="sentinel-s2-l1c")
    except Exception:
        return {"status": "ok"}
