import json

from fastapi import FastAPI, Request
from kafka import KafkaConsumer, KafkaProducer

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello FastAPI!"}


@app.post("/invoke-kafka-consumer")
async def invoke_kafka_consumer(request: Request):
    request_body = await request.json()
    bootstrap_servers = request_body["bootstrap_servers"]
    print(f"bootstrap_servers: {bootstrap_servers}")
    topic = request_body["topic"]
    print(f"topic: {topic}")
    consumer = KafkaConsumer(
        topic,
        bootstrap_servers=bootstrap_servers,
        auto_offset_reset="earliest",
        enable_auto_commit=True,
        group_id="my-group",
        value_deserializer=lambda x: json.loads(x.decode("utf-8")),
        consumer_timeout_ms=500,
    )
    print(f"consumer.bootstrap_connected(): {consumer.bootstrap_connected()}")
    no_messages = 0
    for msg in consumer:
        consumer.commit()
        print(msg)
        no_messages += 1

    assert no_messages == 1

    return {"status": "ok"}


@app.post("/invoke-kafka-producer")
async def invoke_kafka_producer(request: Request):
    request_body = await request.json()
    bootstrap_servers = request_body["bootstrap_servers"]
    print(f"bootstrap_servers: {bootstrap_servers}")
    topic = request_body["topic"]
    print(f"topic: {topic}")
    producer = KafkaProducer(
        bootstrap_servers=bootstrap_servers,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )
    print(f"producer.bootstrap_connected(): {producer.bootstrap_connected()}")
    producer.send(topic, {"foo": "bar"})
    producer.flush()

    return {"status": "ok"}
