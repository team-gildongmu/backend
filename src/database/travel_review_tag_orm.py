from typing import List

from sqlalchemy.sql.schema import Column, ForeignKey
from sqlalchemy.sql.sqltypes import Integer, String

from database.orm import Base
from database.travel_review_orm import TravelReview
from schema.travel_review_request import ReviewTag


class TravelReviewTag(Base):
    __tablename__ = "travel_review_tag"
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    tag = Column(String(256), nullable=False)
    travel_review_id = Column(Integer, ForeignKey("travel_review.id"))
    user_id = Column(Integer, ForeignKey("user.id"))

    @classmethod
    def create(cls, tag: ReviewTag, travel_review: TravelReview, user_id: int) -> "TravelReviewTag":
        return cls(
            tag=tag.name,
            user_id=user_id,
            travel_review_id=travel_review.id,
        )