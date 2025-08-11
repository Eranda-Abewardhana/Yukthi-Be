import os
from datetime import datetime, timedelta
import jwt

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
EXPIRE_MINUTES = 60

def create_jwt(user: dict) -> str:
    to_encode = {
        "sub": user["email"],
        "name": user["name"],
        "exp": datetime.utcnow() + timedelta(minutes=EXPIRE_MINUTES)
    }
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
