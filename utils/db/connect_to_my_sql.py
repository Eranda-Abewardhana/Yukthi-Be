from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

# ✅ MySQL connection string from .env
DATABASE_URL = os.getenv("DATABASE_URL")  # Example: mysql+pymysql://root:pass@localhost/dbname

# ✅ Create engine and session
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
