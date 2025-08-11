import sys
from celery import Celery
import os
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
load_dotenv()




celery_app = Celery(
    "chat_worker",
    broker=os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0"),
    include=['tasks.chat_tasks']
)


celery_app.conf.update(
    task_routes={
        'tasks.chat_tasks.process_chat': {'queue': 'chat_queue'},
    },
    task_track_started=True,
    task_time_limit=300,
)

# No need to import tasks here!
