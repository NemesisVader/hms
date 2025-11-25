from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_caching import Cache
from redis import Redis
from .config import Config

# DATABASE

db = SQLAlchemy()
migrate = Migrate()

# REDIS CLIENT 

redis_client = Redis.from_url(
    Config.REDIS_URL,
    decode_responses=True
)

# FLASK-CACHING (uses Redis)

cache = Cache(config={
    "CACHE_TYPE": "RedisCache",
    "CACHE_REDIS_URL": Config.REDIS_URL,
    "CACHE_DEFAULT_TIMEOUT": 300  # 5 minutes
})
