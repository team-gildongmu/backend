from database.travel_orm import TravelStamp
from database.travel_review_orm import TravelReview


class TravelReviewRepository:
    def __init__(self, session):
        self.session = session

    def create_travel_review(self, travel_review: TravelReview) -> TravelReview:
        self.session.add(instance=travel_review)
        self.session.flush()
        self.session.refresh(instance=travel_review)
        return travel_review
