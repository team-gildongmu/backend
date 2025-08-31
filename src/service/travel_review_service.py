from sqlalchemy.orm.session import Session
from database.travel_review_orm import TravelReview
from database.travel_review_tag_orm import TravelReviewTag
from repository.travel_review_repository import TravelReviewRepository
from repository.travel_review_tag_repository import TravelReviewTagRepository
from schema.travel_review_request import TravelReviewCreateRequest


class TravelReviewService:
    def __init__(self, session: Session):
        self.session = session
        self.travel_review_repo = TravelReviewRepository(session)
        self.travel_review_tag_repo = TravelReviewTagRepository(session)

    def create_travel_review(self, request: TravelReviewCreateRequest, user_id: int):
        travel_review = TravelReview.create(request, user_id)
        saved_travel_review = self.travel_review_repo.create_travel_review(travel_review)

        travel_review_tags = [
            TravelReviewTag.create(tag, saved_travel_review, user_id)
            for tag in request.tag
        ]
        saved_travel_review_tags = self.travel_review_tag_repo.create_travel_review_tags(travel_review_tags)

        return saved_travel_review