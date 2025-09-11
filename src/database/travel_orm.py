from typing import List

from sqlalchemy import Column, Integer, String, Text, Enum, DateTime, ForeignKey
from sqlalchemy.sql.sqltypes import Float, Boolean
from database.base_entity import BaseEntity
from database.orm import Base
from database.travel_location_orm import TravelLocation
from schema.travel_request import TravelLogCreateRequest
from sqlalchemy.orm import relationship

class TravelLog(Base, BaseEntity):
    __tablename__ = "travel_log"
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    title = Column(String(256), nullable=False)
    subtitle = Column(String(256), nullable=False)
    summary = Column(Text, nullable=False)
    theme = Column(String(256), nullable=False)
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

class TravelStamp(Base, BaseEntity) :
    __tablename__ = "travel_stamp"
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    travel_log_id = Column(Integer, ForeignKey("travel_log.id"))
    travel_location_id = Column(Integer, ForeignKey("travel_location.id"))
    user_id = Column(Integer, ForeignKey("user.id"))
    title = Column(String(256), nullable=False)
    is_stamped = Column(Boolean, nullable=False, default=False)
    stamped_at = Column(DateTime, nullable=False)


    location = relationship("TravelLocation", back_populates="stamps")

    @classmethod
    def create_stamp(cls, travel_log: TravelLog, travel_location: TravelLocation) -> "TravelStamp":
        return cls(
            title=travel_location.title,
            travel_log_id=travel_log.id,
            travel_location_id=travel_location.id,
            user_id=travel_log.user_id,
            is_stamped=False
        )

    @classmethod
    def create_stamps(cls, travel_log: TravelLog, travel_locations: List[TravelLocation]) -> List["TravelStamp"]:
        return [
            cls(
                title=location.title,
                travel_log_id=travel_log.id,
                travel_location_id=location.id,
                user_id=travel_log.user_id,
                is_stamped=False
            )
            for location in travel_locations
        ]