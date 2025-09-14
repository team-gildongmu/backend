from typing import List

from database.travel_review_photo_orm import TravelReviewPhoto
from sqlalchemy import select, delete

class TravelReviewPhotoRepository:
    def __init__(self, session):
        self.session = session

    def create_travel_review(self, travel_review_photo: TravelReviewPhoto) -> TravelReviewPhoto:
        self.session.add(instance=travel_review_photo)
        self.session.flush()
        self.session.refresh(instance=travel_review_photo)
        return travel_review_photo

    def get_review_photo_by_review_id(self, review_id: int) -> list[TravelReviewPhoto]:
        stmt = select(TravelReviewPhoto).where(TravelReviewPhoto.travel_review_id == review_id)
        return self.session.scalars(stmt).all()

    def delete_review_photo(self, review_id: int) -> None:
        self.session.execute(delete(TravelReviewPhoto).where(TravelReviewPhoto.travel_review_id == review_id))
        self.session.commit()

    def get_review_photo_by_user_id(self, user_id: int) -> list[TravelReviewPhoto]:
        stmt = select(TravelReviewPhoto).where(TravelReviewPhoto.user_id == user_id)
        return self.session.scalars(stmt).all()