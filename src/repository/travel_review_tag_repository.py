from database.travel_review_tag_orm import TravelReviewTag
from sqlalchemy import select, delete


class TravelReviewTagRepository:
    def __init__(self, session):
        self.session = session

    def create_travel_review_tags(self, travel_review_tags: list[TravelReviewTag]) -> list[TravelReviewTag]:
        self.session.add_all(travel_review_tags)  # bulk insert
        self.session.flush()
        for tag in travel_review_tags:
            self.session.refresh(tag)
        return travel_review_tags

    def delete_review_tag(self, review_id: int) -> None:
        self.session.execute(delete(TravelReviewTag).where(TravelReviewTag.travel_review_id == review_id))
        self.session.commit()