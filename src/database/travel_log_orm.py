from typing import List

from sqlalchemy import Column, Integer, String, Text, Enum, DateTime, ForeignKey
from database.base_entity import BaseEntity
from database.orm import Base
from schema.travel_log_request import TravelLogCreateRequest
from sqlalchemy.orm import relationship

class TravelLog(Base, BaseEntity):
    __tablename__ = "travel_log"
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    title = Column(String(256), nullable=False)
    subtitle = Column(String(256), nullable=False)
    summary = Column(Text, nullable=False)
    theme = Column(String(256), nullable=False)
    locations = relationship("TravelLocation", lazy="joined")
    tags = relationship("TravelLogTag", lazy="joined")

    user_id = Column(Integer, ForeignKey("user.id"))

    @classmethod
    def create(cls, request: TravelLogCreateRequest, user_id: int) -> "TravelLog":
        return cls(
            title=request.title,
            subtitle=request.subtitle,
            summary=request.summary,
            theme=request.theme,
            user_id=user_id,
        )

