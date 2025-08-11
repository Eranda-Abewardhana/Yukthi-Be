FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Adjust module path to your Celery instance
CMD ["bash", "-lc", "celery -A app.tasks.celery_app.celery worker --loglevel=INFO --concurrency=2"]
