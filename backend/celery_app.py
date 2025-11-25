from celery import Celery
from celery.schedules import crontab
from .config import Config

def make_celery():
    celery = Celery(
        "hospital_celery",
        broker=Config.CELERY_BROKER_URL,
        backend=Config.CELERY_RESULT_BACKEND,
        include=["backend.tasks.tasks"]   # auto import tasks
    )

    celery.conf.update(
        timezone="Asia/Kolkata",
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        enable_utc=False,
        broker_connection_retry_on_startup=True,
    )

    # Celery Beat Schedule
    celery.conf.beat_schedule = {
        "daily-reminder-task": {
            "task": "tasks.send_daily_reminders",
            "schedule": crontab(hour=7, minute=0),
        },
        "monthly-report-task": {
            "task": "tasks.send_monthly_reports",
            "schedule": crontab(day_of_month=1, hour=8, minute=0),
        },
    }

    return celery


celery = make_celery()

def get_celery_app():
    return celery
