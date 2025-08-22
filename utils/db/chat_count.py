from datetime import datetime, timedelta
from utils.db.connect_to_my_sql import db

def update_chat_counter(email: str):
    users = db["users"]
    user = users.find_one({"email": email})
    now = datetime.utcnow()

    if not user:
        # Create new user document if not exists
        user = {
            "email": email,
            "chat_window_start": now,
            "chat_request_count": 1,
            "is_cross_limit_per_day": False
        }
        users.insert_one(user)
        return user

    # If no start time or 12+ hours passed → reset window and count
    if not user.get("chat_window_start") or now >= user["chat_window_start"] + timedelta(hours=12):
        update = {
            "$set": {
                "chat_window_start": now,
                "chat_request_count": 1,
                "is_cross_limit_per_day": False
            }
        }
    else:
        # Within 12-hour window → increment
        new_count = user.get("chat_request_count", 0) + 1
        update = {
            "$set": {
                "chat_request_count": new_count,
                "is_cross_limit_per_day": new_count > 7
            }
        }
    users.update_one({"email": email}, update)
    return users.find_one({"email": email})
