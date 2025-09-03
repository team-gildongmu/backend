from database.travel_review_photo_orm import TravelReviewPhoto


class TravelReviewPhotoRepository:
    def __init__(self, session):
        self.session = session

    def create_travel_review(self, travel_review_photo: TravelReviewPhoto) -> TravelReviewPhoto:
        self.session.add(instance=travel_review_photo)
        self.session.flush()
        self.session.refresh(instance=travel_review_photo)
        return travel_review_photo