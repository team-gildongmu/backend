from typing import List

from sqlalchemy import Column, Integer, String, Text, Enum, DateTime, ForeignKey
from sqlalchemy.sql.sqltypes import Float, Boolean
from database.base_entity import BaseEntity
from database.orm import Base
from schema.travel_request import TravelLogCreateRequest, TravelLocationCreateRequest


class TravelLog(Base, BaseEntity):
    __tablename__ = "travel_log"
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    title = Column(String(256), nullable=False)
    user_id = Column(Integer, ForeignKey("user.id"))

    @classmethod
    def create(cls, request: TravelLogCreateRequest, user_id: int) -> "TravelLog":
        return cls(
            title=request.title,
            user_id=user_id,
        )


class TravelLocation(Base, BaseEntity) :
    __tablename__ = "travel_location"
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    travel_log_id = Column(Integer, ForeignKey("travel_log.id"))
    user_id = Column(Integer, ForeignKey("user.id"))
    name = Column(String(256), nullable=False)
    sequence = Column(Integer, nullable=False)
    longitude = Column(Float, nullable=False)
    latitude = Column(Float, nullable=False)
    congestion = Column(String(256), nullable=False)

    @classmethod
    def create(cls, request: TravelLocationCreateRequest, travel_log: TravelLog) -> "TravelLocation":
        return cls(
            name=request.name,
            sequence=request.sequence,
            longitude=request.longitude,
            latitude=request.latitude,
            congestion=request.congestion,
            travel_log_id=travel_log.id,
            user_id=travel_log.user_id,
        )


class TravelStamp(Base, BaseEntity) :
    __tablename__ = "travel_stamp"
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    travel_log_id = Column(Integer, ForeignKey("travel_log.id"))
    travel_location_id = Column(Integer, ForeignKey("travel_location.id"))
    user_id = Column(Integer, ForeignKey("user.id"))
    title = Column(String(256), nullable=False)
    is_stamped = Column(Boolean, nullable=False)
    stamped_at = Column(DateTime, nullable=False)

    @classmethod
    def create_stamps(cls, travel_log: TravelLog, travel_locations: List[TravelLocation]) -> List["TravelStamp"]:
        return [
            cls(
                title=location.name,
                travel_log_id=travel_log.id,
                travel_location_id=location.id,
                user_id=travel_log.user_id,
            )
            for location in travel_locations
        ]