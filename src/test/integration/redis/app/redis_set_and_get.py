import os

import redis

client = redis.StrictRedis(host=os.getenv("REDIS_HOST"), port=os.getenv("REDIS_PORT"))
client.set("my-key", "my-value")
client.get("my-key")
