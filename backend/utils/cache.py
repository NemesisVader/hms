from ..extensions import redis_client
import json


def cache_get(key):
    value = redis_client.get(key)
    if value:
        return json.loads(value)
    return None


def cache_set(key, value, expire=300):
    redis_client.set(key, json.dumps(value), ex=expire)


def cache_delete(key):
    redis_client.delete(key)
