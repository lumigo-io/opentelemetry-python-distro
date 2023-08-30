import os

import redis

client = redis.StrictRedis(host=os.getenv("REDIS_HOST"), port=os.getenv("REDIS_PORT"))
pipe = client.pipeline()
pipe.set("my-key", "pre-key-value").get("my-key")
pipe.set("my-key", "key-value").get("my-key")
pipe.get("unknown-key")
pipe.execute()
