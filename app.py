import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine
from starlette.middleware.sessions import SessionMiddleware
from starlette.staticfiles import StaticFiles
from databases.my_sql.user_table import Base
from routes.chat_routes import chat_router
from routes.login_routes import login_router
from routes.payments_routes import payment_router
import uvicorn
app = FastAPI()
load_dotenv()
BASE_URL = os.getenv("BASE_URL_ONLY", "http://localhost")
PORT = int(os.getenv("PORT", 9000))

engine = create_engine(os.getenv("DATABASE_URL"))
Base.metadata.create_all(engine)
# ✅ CORS origins
origins = [
    "*",  # Update this to your frontend URL in production
]

# ✅ Add CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Add SessionMiddleware (only accepts `secret_key`)
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SECRET_KEY"),
    same_site="lax",  # Helps with cross-site cookies in localhost
    https_only=False  # Set to True if using HTTPS
)
# ✅ Routers
app.include_router(chat_router)
app.include_router(login_router)
app.include_router(payment_router)

# ✅ Static files mount
app.mount("/data_sources", StaticFiles(directory="data_sources"), name="data_sources")

# ✅ Run server locally (for development)
if __name__ == "__main__":
    uvicorn.run(app, host=BASE_URL, port=PORT)
