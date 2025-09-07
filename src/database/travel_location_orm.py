from typing import List

from sqlalchemy import Column, Integer, String, Text, Enum, DateTime, ForeignKey
from sqlalchemy.sql.sqltypes import Float, Boolean
from database.base_entity import BaseEntity
from database.orm import Base
from schema.travel_request import TravelLocationCreateRequest

class TravelLocation(Base, BaseEntity) :
    __tablename__ = "travel_location"
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    travel_log_id = Column(Integer, ForeignKey("travel_log.id"))
    user_id = Column(Integer, ForeignKey("user.id"))
    title = Column(String(256), nullable=False)
    longitude = Column(Float, nullable=False)
    latitude = Column(Float, nullable=False)
    location_type = Column(String(256), nullable=False)
    description = Column(Text, nullable=False)
    reason = Column(Text, nullable=False)
    image_link = Column(String(256))

    sequence = Column(Integer)
    congestion = Column(String(256))

    @classmethod
    def create(cls, request: TravelLocationCreateRequest, travel_log_id: int, user_id: int, image_link: str) -> "TravelLocation":
        return cls(
            title=request.title,
            longitude=float(request.coords.mapx),
            latitude = float(request.coords.mapy),
            location_type=request.type,
            description=request.desc,
            reason=request.reason,
            travel_log_id=travel_log_id,
            user_id=user_id,
            image_link=image_link

            # sequence=request.sequence,
            # congestion=request.congestion,
        )


