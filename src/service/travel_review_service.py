import os
import uuid
from datetime import datetime
from http.client import HTTPException
from typing import Optional

from sqlalchemy.orm.session import Session
from database.travel_review_orm import TravelReview
from database.travel_review_photo_orm import TravelReviewPhoto
from database.travel_review_tag_orm import TravelReviewTag
from repository.travel_review_photo_repository import TravelReviewPhotoRepository
from repository.travel_review_repository import TravelReviewRepository
from repository.travel_review_tag_repository import TravelReviewTagRepository
from schema.travel_review_request import TravelReviewCreateRequest
from utils.aws_client import AWSBotoClient


class TravelReviewService:
    def __init__(self, session: Session):
        self.session = session
        self.travel_review_repo = TravelReviewRepository(session)
        self.travel_review_tag_repo = TravelReviewTagRepository(session)
        self.travel_review_photo_repo = TravelReviewPhotoRepository(session)
        self.s3_client = AWSBotoClient()

    def create_travel_review(self, request: TravelReviewCreateRequest, user_id: int):
        travel_review = TravelReview.create(request, user_id)
        saved_travel_review = self.travel_review_repo.create_travel_review(travel_review)

        travel_review_tags = [
            TravelReviewTag.create(tag, saved_travel_review, user_id)
            for tag in request.tag
        ]

        saved_travel_review_tags = self.travel_review_tag_repo.create_travel_review_tags(travel_review_tags)

        # review_photo_key: Optional[str] = None

        for picture in request.picture:
            original_name = picture.filename or "upload"
            _, dot, ext = original_name.rpartition('.')
            ext = f".{ext}" if dot else ""
            timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%S%fZ")
            unique_id = uuid.uuid4().hex
            file_name = f"{timestamp}_{unique_id}{ext}"

            folder_name = "review_pics"
            review_photo_key = f"{folder_name}/{user_id}/{file_name}"

            self.s3_client.upload_file(folder_name, user_id, file_name, picture.file)

            #profile_photo_url = self.s3_client.get_file(review_photo_key)

            travel_review_photo = TravelReviewPhoto.create(review_photo_key, saved_travel_review, user_id)
            self.travel_review_photo_repo.create_travel_review(travel_review_photo)

        return saved_travel_review

    def delete_travel_review(self, travel_review_id: int):
        travel_review: TravelReview | None = self.travel_review_repo.get_review_by_review_id(travel_review_id)
        if not travel_review:
            raise Exception("Travel Review Not Found")

        review_photos = self.travel_review_photo_repo.get_review_photo_by_review_id(review_id=travel_review_id)
        for photo in review_photos or []:
            file_name = os.path.basename(photo.review_photo_link)
            self.s3_client.delete_file(photo.review_photo_link)

        self.travel_review_photo_repo.delete_review_photo(travel_review_id)
        self.travel_review_tag_repo.delete_review_tag(travel_review_id)

        self.travel_review_repo.delete_review(travel_review_id)
