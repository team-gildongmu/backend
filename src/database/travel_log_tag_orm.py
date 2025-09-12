from sqlalchemy import Column, Integer, String, Text, Enum, DateTime, ForeignKey
from database.orm import Base
from database.travel_log_orm import TravelLog

class TravelLogTag(Base):
    __tablename__ = "travel_log_tag"
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    tag = Column(String(256), nullable=False)
    travel_log_id = Column(Integer, ForeignKey("travel_log.id"))
    user_id = Column(Integer, ForeignKey("user.id"))

    @classmethod
    def create(cls, tag: String, travel_log: TravelLog, user_id: int) -> "TravelLogTag":
        return cls(
            tag=tag,
            user_id=user_id,
            travel_log_id=travel_log.id,
        )
