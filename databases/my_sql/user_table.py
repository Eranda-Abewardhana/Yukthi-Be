from sqlalchemy import Column, String, Boolean, DateTime, Integer
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime, timedelta

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    email = Column(String(255), primary_key=True, index=True)
    is_has_account = Column(Boolean, default=False)
    is_cross_limit_per_day = Column(Boolean, default=False)
    expired_at = Column(DateTime, default=lambda: None)
    chat_window_start = Column(DateTime, nullable=True)
    chat_request_count = Column(Integer, default=0)
    is_premium = Column(Boolean, default=False)
    premium_expire_at = Column(DateTime, nullable=True)

