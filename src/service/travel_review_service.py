from sqlalchemy.orm.session import Session
from database.travel_review_orm import TravelReview
from repository.travel_review_repository import TravelReviewRepository
from schema.travel_review_request import TravelReviewCreateRequest


class TravelReviewService:
    def __init__(self, session: Session):
        self.session = session
        self.travel_review_repo = TravelReviewRepository(session)

    def create_travel_review(self, request: TravelReviewCreateRequest, user_id: int):
        travel_review = TravelReview.create(request, user_id)
        saved_travel_review = self.travel_review_repo.create_travel_review(travel_review)
        return saved_travel_review