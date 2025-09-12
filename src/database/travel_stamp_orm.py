from typing import List

from sqlalchemy import Column, Integer, String, Text, Enum, DateTime, ForeignKey
from sqlalchemy.sql.sqltypes import Float, Boolean
from database.base_entity import BaseEntity
from database.orm import Base
from database.travel_location_orm import TravelLocation
from sqlalchemy.orm import relationship

from database.travel_log_orm import TravelLog


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