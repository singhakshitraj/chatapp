from celery import Celery
import os
from dotenv import load_dotenv

load_dotenv()

celery_app=Celery(
    "worker",
    broker=os.environ.get('REDIS_URL'),
)

celery_app.autodiscover_tasks(['utils.send_email'])