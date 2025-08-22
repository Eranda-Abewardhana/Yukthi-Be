from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

# MongoDB connection string from .env
DATABASE_URL = os.getenv("DATABASE_URL")  # Example: mongodb://localhost:27017/yukti

client = MongoClient(DATABASE_URL)
db = client.get_default_database()  # This will use 'yukti' as the database name
