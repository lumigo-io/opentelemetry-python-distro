import os

import redis

client = redis.StrictRedis(host=os.getenv("REDIS_HOST"), port=os.getenv("REDIS_PORT"))
client.hmset("my-key", {"key1": "value1", "key2": "value2"})
client.hgetall("my-key")
