from typing import List

from sqlalchemy import Column, Integer, String, Text, Enum, DateTime, ForeignKey
from sqlalchemy.sql.sqltypes import Float, Boolean
from database.orm import Base
from schema.travel_request import StayCreateRequest

class TravelStay(Base):
    __tablename__ = "travel_stay"
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    title = Column(String(256), nullable=False)
    description = Column(Text, nullable=False)
    longitude = Column(Float, nullable=False)
    latitude = Column(Float, nullable=False)
    image_link = Column(String(256))
    user_id = Column(Integer, ForeignKey("user.id"))
    travel_log_id = Column(Integer, ForeignKey("travel_log.id"))

    @classmethod
    def create(cls, request: StayCreateRequest, travel_log_id: int, user_id: int, image_link: str) -> "TravelLocation":
        return cls(
            title=request.title,
            longitude=float(request.coords.mapx),
            latitude=float(request.coords.mapy),
            description=request.desc,
            image_link=image_link,
            travel_log_id=travel_log_id,
            user_id=user_id,
        )