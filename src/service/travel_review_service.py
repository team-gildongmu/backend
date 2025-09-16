import os
import uuid
from datetime import datetime
from http.client import HTTPException
from typing import Optional, List

from sqlalchemy.orm.session import Session

from api import travel_review
from database.travel_review_orm import TravelReview
from database.travel_review_photo_orm import TravelReviewPhoto
from database.travel_review_tag_orm import TravelReviewTag
from repository.travel_review_photo_repository import TravelReviewPhotoRepository
from repository.travel_review_repository import TravelReviewRepository
from repository.travel_review_tag_repository import TravelReviewTagRepository
from repository.user_repository import UserRepository
from schema.travel_review_request import WEATHER_LABELS, REVIEW_TAG_LABELS
from schema.travel_review_response import TravelReviewListResponse, TravelReviewCalendarResponse, TravelReviewResponse
from schema.travel_review_request import TravelReviewCreateRequest, TravelReviewUpdateRequest
from utils.aws_client import AWSBotoClient


class TravelReviewService:
    def __init__(self, session: Session):
        self.session = session
        self.travel_review_repo = TravelReviewRepository(session)
        self.travel_review_tag_repo = TravelReviewTagRepository(session)
        self.travel_review_photo_repo = TravelReviewPhotoRepository(session)
        self.user_repo = UserRepository(session)
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

    def get_travel_review(self, travel_review_id: int) -> TravelReviewResponse:
        travel_review = self.travel_review_repo.get_review_by_review_id(travel_review_id)

        image_urls = []
        for photo in travel_review.photos or []:
            s3_url = self.s3_client.get_file(photo.review_photo_link)
            image_urls.append(s3_url)

        tags = []
        for tag in travel_review.tags or []:
            tags.append(REVIEW_TAG_LABELS.get(tag.tag, tag.tag))

        response= TravelReviewResponse(
            travel_review_id=travel_review.id,
            title=travel_review.title,
            ai_rating=travel_review.ai_rating,
            start_date=travel_review.started_at,
            end_date=travel_review.finished_at,
            weather=WEATHER_LABELS.get(travel_review.weather, travel_review.weather),
            images=image_urls,
            tags=tags,
            mood=travel_review.mood,
            note=travel_review.note,
        )

        return response

    def get_travel_review_list(self, user_id: int) -> List[TravelReviewListResponse]:
        user_profile = self.user_repo.get_profile(user_id)
        user_photo_url = self.s3_client.get_file(user_profile.profile_photo_key) if user_profile.profile_photo_key else None

        travel_reviews = self.travel_review_repo.get_review_by_user_id(user_id)
        result = []

        for travel_review in travel_reviews or []:
            # 각 사진의 S3 URL 생성
            image_urls = []
            for photo in travel_review.photos or []:
                s3_url = self.s3_client.get_file(photo.review_photo_link)
                image_urls.append(s3_url)

            tags = []
            for tag in travel_review.tags or []:
                tags.append(REVIEW_TAG_LABELS.get(tag.tag, tag.tag))

            response_item = TravelReviewListResponse(
                travel_review_id=travel_review.id,
                user_nickname=user_profile.nickname,
                user_photo=user_photo_url,
                title=travel_review.title,
                ai_rating=travel_review.ai_rating,
                start_date=travel_review.started_at,
                end_date=travel_review.finished_at,
                weather=WEATHER_LABELS.get(travel_review.weather, travel_review.weather),
                image=image_urls,
                tags=tags,
                note=travel_review.note,
            )
            result.append(response_item)

        return result

    def get_travel_review_calendar(self, user_id: int) -> List[TravelReviewCalendarResponse]:
        travel_reviews = self.travel_review_repo.get_review_by_user_id(user_id)
        result = []

        for travel_review in travel_reviews or []:
            response_item = TravelReviewCalendarResponse(
                travel_review_id=travel_review.id,
                title=travel_review.title,
                start_date=travel_review.started_at,
                end_date=travel_review.finished_at,
            )
            result.append(response_item)

        return result

    def update_travel_review(self,  request: TravelReviewUpdateRequest, user_id: int):
        travel_review: TravelReview | None = self.travel_review_repo.get_review_by_review_id(request.review_id)

        if not travel_review:
            raise Exception("Review not found")

        if travel_review.user_id != user_id:
            raise Exception("Not allowed to update this review")

        travel_review.update_review(request)

        self.travel_review_tag_repo.delete_review_tag(travel_review.id)
        travel_review_tags = [
            TravelReviewTag.create(tag, travel_review, user_id)
            for tag in request.tag
        ]
        saved_travel_review_tags = self.travel_review_tag_repo.create_travel_review_tags(travel_review_tags)

        review_photos = self.travel_review_photo_repo.get_review_photo_by_review_id(review_id=travel_review.id)
        for photo in review_photos or []:
            file_name = os.path.basename(photo.review_photo_link)
            self.s3_client.delete_file(photo.review_photo_link)
        self.travel_review_photo_repo.delete_review_photo(review_id=travel_review.id)

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

            # profile_photo_url = self.s3_client.get_file(review_photo_key)

            travel_review_photo = TravelReviewPhoto.create(review_photo_key, travel_review, user_id)
            self.travel_review_photo_repo.create_travel_review(travel_review_photo)

