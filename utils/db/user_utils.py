from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from databases.my_sql.user_table import User


def reset_cross_limit_if_expired(user: User, db: Session):

    if user :
        if user.expired_at == None :
            user.expired_at = datetime.utcnow() + timedelta(hours=12)
            return user
        if datetime.utcnow() >= user.expired_at:
            user.is_cross_limit_per_day = False
            user.expired_at = datetime.utcnow()
            db.commit()
            db.refresh(user)

    return user

def expire_premium_if_overdue(user: User, db: Session) -> bool:
    """
    Expires premium status if the current time is past the premium_expire_at.
    Returns True if premium was expired, False otherwise.
    """
    if user.is_premium and user.premium_expire_at:
        if datetime.utcnow() > user.premium_expire_at:
            user.is_premium = False
            user.premium_expire_at = None
            db.commit()
            db.refresh(user)
            return True  # ✅ Premium expired
    return False  # ✅ Still active or not premium

def check_and_update_premium_status(user: User, db: Session) -> User:
    """
    Checks if the user's premium status has expired and updates the user accordingly.
    """
    now = datetime.utcnow()

    if user.is_premium and user.premium_expire_at:
        if now > user.premium_expire_at:
            print(f"🔁 Premium expired for user: {user.email}")
            user.is_premium = False
            db.commit()
            db.refresh(user)

    return user

def create_user_if_not_exists(email: str, db: Session) -> User:
    """
    Creates a new user in the database if the user doesn't already exist.
    Returns the existing or newly created user.
    """
    user = db.query(User).filter(User.email == email).first()

    if not user:
        user = User(
            email=email,
            is_has_account=True,
            is_cross_limit_per_day=False,
            expired_at=None,
            chat_window_start=None,
            chat_request_count=0,
            is_premium=False,
            premium_expire_at=None
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    return user