from testcontainers.mongodb import MongoDbContainer

import motor.motor_asyncio


async def do_insert():
    document = {"my-k": "my-value"}
    result = await db.test_collection.insert_one(document)
    print(f"result {result.inserted_id}")


async def do_find_one():
    document = await db.test_collection.find_one()
    print("found", document)


with MongoDbContainer("mongo:4") as mongo:
    client = motor.motor_asyncio.AsyncIOMotorClient(mongo.get_connection_url())
    db = client.test

    loop = client.get_io_loop()
    loop.run_until_complete(do_insert())
    loop.run_until_complete(do_find_one())
