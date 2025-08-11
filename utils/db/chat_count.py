from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from databases.my_sql.user_table import User

def update_chat_counter(user: User, db: Session):
    now = datetime.utcnow()

    # If no start time or 12+ hours passed → reset window and count
    if not user.chat_window_start or now >= user.chat_window_start + timedelta(hours=12):
        user.chat_window_start = now
        user.chat_request_count = 1
        user.is_cross_limit_per_day = False
    else:
        # Within 12-hour window → increment
        user.chat_request_count += 1

        # Check if limit exceeded
        if user.chat_request_count > 7:
            user.is_cross_limit_per_day = True

    db.commit()
    db.refresh(user)
    return user
