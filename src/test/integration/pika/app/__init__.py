import pika
from fastapi import FastAPI, Request

app = FastAPI()
test_message = "Hello World!"
topic = "pika-topic"


@app.get("/")
async def root():
    return {"message": "Hello FastAPI!"}


@app.post("/invoke-pika-consumer")
async def invoke_pika_consumer(request: Request):
    connection_params = await request.json()
    print(f"connection_params: {connection_params}")
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host=connection_params["host"], port=connection_params["port"]
        )
    )
    print("consumer connection created")
    channel = connection.channel()
    print(f"consumer connection.is_open: {connection.is_open}")
    channel.queue_declare(queue=topic)
    (method, properties, body) = channel.basic_get(queue=topic, auto_ack=True)
    assert method is not None and properties is not None and body is not None
    received_message = str(body, "utf-8")
    assert received_message == test_message
    print(f"message received: {received_message}")

    return {"status": "ok"}


@app.post("/invoke-pika-producer")
async def invoke_pika_producer(request: Request):
    connection_params = await request.json()
    print(f"connection_params: {connection_params}")
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host=connection_params["host"], port=connection_params["port"]
        )
    )
    print("producer connection created")
    channel = connection.channel()
    print(f"producer connection.is_open: {connection.is_open}")
    channel.queue_declare(queue=topic)
    channel.basic_publish(exchange="", routing_key=topic, body=test_message)

    connection.close()

    return {"status": "ok"}
