from sqlalchemy import select, delete

from database.travel_review_orm import TravelReview


class TravelReviewRepository:
    def __init__(self, session):
        self.session = session

    def create_travel_review(self, travel_review: TravelReview) -> TravelReview:
        self.session.add(instance=travel_review)
        self.session.flush()
        self.session.refresh(instance=travel_review)
        return travel_review

    def get_review_by_review_id(self, review_id: int) -> TravelReview | None:
        return self.session.scalar(select(TravelReview).where(TravelReview.id == review_id))

    def delete_review(self, review_id: int) -> None:
        self.session.execute(delete(TravelReview).where(TravelReview.id == review_id))
        self.session.commit()