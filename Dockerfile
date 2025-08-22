FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# If you use mysqlclient instead of PyMySQL, add build deps. PyMySQL needs none.
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Expose for local; Railway will map $PORT automatically.
EXPOSE 8000

# Use $PORT if provided (Railway), else default to 8000 (local/docker-compose)
CMD ["bash", "-lc", "uvicorn app:app --host 0.0.0.0 --port ${PORT:-8000}"]
