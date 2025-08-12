from typing import List

from sqlalchemy import Column, Integer, String, Text, Enum, DateTime, ForeignKey
from sqlalchemy.sql.sqltypes import Float, Boolean
from database.base_entity import BaseEntity
from database.orm import Base
from schema.travel_request import TravelLogCreateRequest, TravelLocationCreateRequest
from schema.travel_review_request import TravelReviewCreateRequest


class TravelReview(Base, BaseEntity) :
    __tablename__ = "travel_review"
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    travel_log_id = Column(Integer, ForeignKey("travel_log.id"))
    user_id = Column(Integer, ForeignKey("user.id"))
    title = Column(String(256), nullable=False)
    ai_rating = Column(Float, nullable=False)
    started_at = Column(String(256), nullable=False)
    finished_at = Column(String(256), nullable=False)
    weather = Column(String(256), nullable=False) #추후 enum으로 관리
    mood = Column(String(256), nullable=False)  #추후 enum으로 관리
    tag = Column(String(256), nullable=False) #여러개 선택 가능한지 확인
    note = Column(Text, nullable=False)
    song = Column(String(256), nullable=False) #추후 논의 필요


    @classmethod
    def create(cls, request: TravelReviewCreateRequest, user_id: int) -> "TravelReview":
        return cls(
            travel_log_id=request.travel_log_id,
            user_id=user_id,
            title=request.title,
            ai_rating=request.ai_rating,
            started_at=request.started_at,
            finished_at=request.finished_at,
            weather=request.weather,
            mood=request.mood,
            tag=request.tag,
            note=request.note,
            song=request.song,
        )
