from datetime import datetime, timedelta
from utils.db.connect_to_my_sql import db


def reset_cross_limit_if_expired(email: str):
    users = db["users"]
    user = users.find_one({"email": email})
    if user:
        if user.get("expired_at") is None:
            users.update_one({"email": email}, {"$set": {"expired_at": datetime.utcnow() + timedelta(hours=12)}})
            user = users.find_one({"email": email})
            return user
        if datetime.utcnow() >= user["expired_at"]:
            users.update_one({"email": email}, {"$set": {"is_cross_limit_per_day": False, "expired_at": datetime.utcnow()}})
            user = users.find_one({"email": email})
    return user


def expire_premium_if_overdue(email: str) -> bool:
    users = db["users"]
    user = users.find_one({"email": email})
    if user and user.get("is_premium") and user.get("premium_expire_at"):
        if datetime.utcnow() > user["premium_expire_at"]:
            users.update_one({"email": email}, {"$set": {"is_premium": False, "premium_expire_at": None}})
            return True  # Premium expired
    return False  # Still active or not premium


def check_and_update_premium_status(email: str):
    users = db["users"]
    user = users.find_one({"email": email})
    now = datetime.utcnow()
    if user and user.get("is_premium") and user.get("premium_expire_at"):
        if now > user["premium_expire_at"]:
            print(f"\u21bb Premium expired for user: {user['email']}")
            users.update_one({"email": email}, {"$set": {"is_premium": False}})
            user = users.find_one({"email": email})
    return user


def create_user_if_not_exists(email: str):
    users = db["users"]
    user = users.find_one({"email": email})
    if not user:
        user = {
            "email": email,
            "is_has_account": True,
            "is_cross_limit_per_day": False,
            "expired_at": None,
            "chat_window_start": None,
            "chat_request_count": 0,
            "is_premium": False,
            "premium_expire_at": None
        }
        users.insert_one(user)
    return users.find_one({"email": email})
