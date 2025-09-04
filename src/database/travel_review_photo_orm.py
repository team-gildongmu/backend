from sqlalchemy.sql.schema import Column, ForeignKey
from sqlalchemy.sql.sqltypes import Integer, String

from database.orm import Base
from database.travel_review_orm import TravelReview



class TravelReviewPhoto(Base):
    __tablename__ = "travel_review_photo"
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    travel_review_id = Column(Integer, ForeignKey("travel_review.id"))
    user_id = Column(Integer, ForeignKey("user.id"))
    review_photo_link = Column(String(256), nullable=False)

    @classmethod
    def create(cls, review_photo_link: str, travel_review: TravelReview, user_id: int) -> "TravelReviewPhoto":
        return cls(
            review_photo_link=review_photo_link,
            user_id=user_id,
            travel_review_id=travel_review.id,
        )