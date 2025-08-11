# Yukti Backend (FastAPI + Celery + MySQL)

Yukti is an AI-powered legal chatbot for Sri Lankan law.  
This backend exposes REST APIs (FastAPI), runs background tasks (Celery), retrieves legal sources via a RAG pipeline (AutomergingRetriever + LlamaIndex), and performs multi-agent Tree-of-Thoughts (ToT) reasoning over Groq-hosted LLMs.

> **Disclaimer:** Yukti provides information only. It is **not** a substitute for legal advice.

---

## ✨ Features

- **FastAPI** HTTP API with OpenAPI docs
- **OAuth (Google)** login (JWT sessions)
- **RAG**: LlamaIndex + AutomergingRetriever over indexed legal corpora
- **Reasoning**: Tree-of-Thoughts (multi-agent, multi-depth)
- **Groq** LLMs (e.g., Llama 3B)
- **Celery** workers for parallel chat processing
- **MySQL** persistence
- **CI/CD** via GitHub Actions → **AWS ECS** deploys

---

## 🗂 Project Structure (suggested)

backend/
app/
api/
v1/
routes_chat.py
routes_auth.py
core/
config.py
security.py
db/
base.py
models/
session.py
migrations/ # (Alembic if used)
rag/
index_builder.py
retriever.py
reasoning/
tot.py # Tree-of-Thoughts orchestration
agents.py
services/
auth.py
chat.py
citations.py
tasks/
celery_app.py
chat_tasks.py
main.py # FastAPI entrypoint
tests/
requirements.txt or pyproject.toml
Dockerfile
celery.Dockerfile
README.backend.md

yaml
Copy
Edit

---

## 🔧 Requirements

- Python 3.10+
- MySQL 8.x (or Aurora MySQL)
- Redis or RabbitMQ for Celery broker/result backend
- Groq API key
- Google OAuth credentials

---

## 🔐 Environment Variables

Create `.env` in `backend/`:

FastAPI
APP_ENV=prod
APP_HOST=0.0.0.0
APP_PORT=8000
APP_CORS_ORIGINS=http://localhost:5173,https://your-frontend.example.com
SECRET_KEY=change_me

DB
MYSQL_USER=yukti
MYSQL_PASSWORD=change_me
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_DB=yukti

Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1
CELERY_CONCURRENCY=4
CELERY_TASK_SOFT_TIME_LIMIT=60
CELERY_TASK_HARD_TIME_LIMIT=90

Auth (Google)
GOOGLE_CLIENT_ID=xxx.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=xxx
OAUTH_REDIRECT_URI=http://localhost:5173/auth/callback

LLM (Groq)
GROQ_API_KEY=xxx
GROQ_MODEL=llama3-8b-instruct

RAG / LlamaIndex
LLAMA_INDEX_DIR=./storage/index
RAG_TOP_K=5
AUTOMERGE_MAX_CHUNK_SIZE=1200

Reasoning (ToT)
TOT_NUM_AGENTS=3
TOT_MAX_DEPTH=4
TOT_BRANCH_FACTOR=3
TOT_EVALUATION_STRATEGY=voting # or score
TOT_TEMPERATURE=0.3

Observability
LOG_LEVEL=INFO


> If you use Alembic: `DATABASE_URL=mysql+pymysql://yukti:change_me@localhost:3306/yukti`

---

## ▶️ Local Development

```bash
# 1) Create & activate venv
python -m venv .venv && source .venv/bin/activate

# 2) Install deps
pip install -r requirements.txt   # or: pip install -e . if using pyproject

# 3) (Optional) Initialize DB schema
alembic upgrade head              # only if Alembic is set up

# 4) Build or refresh the RAG index
python -m app.rag.index_builder --source ./data/sri_lanka_law --out $LLAMA_INDEX_DIR

# 5) Run API
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 6) In a separate shell, run Celery worker
celery -A app.tasks.celery_app.celery worker --loglevel=INFO --concurrency=${CELERY_CONCURRENCY:-2}"# Yukthi-Be" 
