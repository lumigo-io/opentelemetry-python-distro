from fastapi import FastAPI
from pymongo import MongoClient
from testcontainers.mongodb import MongoDbContainer


app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello FastAPI!"}


@app.get("/invoke-mongo")
def invoke_mongo():
    with MongoDbContainer() as mongo:
        mongo.get_connection_client().test  # Wait that is is connected

        db = MongoClient(mongo.get_connection_url()).test

        doc = {
            "address": {
                "street": "2 Avenue",
            },
            "restaurant_id": "41704620",
        }

        result = db.items.insert_one(doc)

        assert result.acknowledged

        assert db.items.find_one() == doc

    return {"status": "ok"}
