from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_caching import Cache
from redis import Redis
from .config import Config

db = SQLAlchemy()
migrate = Migrate()

redis_client = Redis.from_url(
    Config.REDIS_URL,
    decode_responses=True
)

cache = Cache(config={
    "CACHE_TYPE": "RedisCache",
    "CACHE_REDIS_URL": Config.REDIS_URL,
    "CACHE_DEFAULT_TIMEOUT": 300
})
