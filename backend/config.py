class Config:
    SECRET_KEY = "a1b2c3d4e5f60718293a4b5c6d7e8f90"
    SQLALCHEMY_DATABASE_URI = "sqlite:///hospital.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    REDIS_URL = "redis://localhost:6379/0"
    CELERY_BROKER_URL = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND = "redis://localhost:6379/2"
