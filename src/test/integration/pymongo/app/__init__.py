from fastapi import FastAPI
from testcontainers.mongodb import MongoDbContainer


app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello FastAPI!"}


@app.get("/invoke-mongo")
def invoke_mongo():
    with MongoDbContainer() as mongo:
        db = mongo.get_connection_client().test
        doc = {
            "address": {
                "street": "2 Avenue",
            },
            "restaurant_id": "41704620",
        }
        db.items.insert_one(doc)
    return {"status": "ok"}
