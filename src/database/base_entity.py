import pytz
from sqlalchemy import Column, DateTime, Integer
from datetime import datetime, timezone
from sqlalchemy.ext.declarative import declared_attr

# 한국 시간대
KST = pytz.timezone('Asia/Seoul')

def kst_now():
    return datetime.now(KST)

class BaseEntity:
    created_at = Column(DateTime(timezone=True), default=kst_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=kst_now, onupdate=kst_now, nullable=False)
    # created_by = Column(Integer, nullable=True)
    # updated_by = Column(Integer, nullable=True)

    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()  # 필요시 제거 가능