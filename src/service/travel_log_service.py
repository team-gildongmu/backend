import uuid
import os
from collections import defaultdict

from sqlalchemy.orm.session import Session
from datetime import datetime
from database.travel_location_orm import TravelLocation
from database.travel_log_orm import TravelLog
from database.travel_stamp_orm import TravelStamp
from database.travel_stay_orm import TravelStay
from database.travel_log_tag_orm import TravelLogTag
from repository.travel_location_repository import TravelLocationRepository
from repository.travel_log_repository import TravelLogRepository
from repository.travel_log_tag_repository import TravelLogTagRepository
from repository.travel_stamp_repository import TravelStampRepository
from repository.travel_stay_repository import TravelStayRepository
from schema.travel_location_response import TravelLocationResponse, TravelLocationMapResponse
from schema.travel_log_request import TravelLogCreateRequest
from schema.travel_log_response import TravelLogListResponse, TravelLogResponse, TravelLogMapResponse
from utils.aws_client import AWSBotoClient

class TravelLogService:
    def __init__(self, session: Session):
        self.session = session
        self.travel_log_repo = TravelLogRepository(session)
        self.travel_log_tag_repo = TravelLogTagRepository(session)
        self.travel_location_repo = TravelLocationRepository(session)
        self.travel_stay_repo = TravelStayRepository(session)
        self.travel_stamp_repo = TravelStampRepository(session)
        self.s3_client = AWSBotoClient()
        self.radius_km = float(os.getenv("STAMP_RADIUS_KM", 2))

    def create_travel_log(self, request: TravelLogCreateRequest, user_id: int):

        uploaded_file_names = []

        try:
            travel_log = TravelLog.create(request, user_id)
            saved_travel_log = self.travel_log_repo.create_travel_log(travel_log)

            travel_log_tags = [
                TravelLogTag.create(keyword, saved_travel_log, user_id)
                for keyword in request.keywords
            ]

            self.travel_log_tag_repo.create_travel_log_tags(travel_log_tags)

            travel_day = 0
            for day in request.days:
                travel_day += 1
                for location in day.segments:
                    url = location.image or "upload"
                    _, dot, ext = url.rpartition('.')
                    ext = f".{ext}" if dot else ""
                    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%S%fZ")
                    unique_id = uuid.uuid4().hex
                    file_name = f"{timestamp}_{unique_id}{ext}"

                    folder_name = "location_pics"
                    location_image_key = f"{folder_name}/{user_id}/{file_name}"

                    self.s3_client.upload_file_from_url(folder_name, user_id, file_name, url)
                    uploaded_file_names.append(location_image_key)

                    travel_location = TravelLocation.create(location, saved_travel_log.id, user_id, location_image_key, travel_day)
                    saved_travel_location = self.travel_location_repo.create_travel_location(travel_location)

                    travel_stamp = TravelStamp.create_stamp(saved_travel_log, saved_travel_location)
                    self.travel_stamp_repo.create_travel_stamp(travel_stamp)

            for stay in request.stays:
                url = stay.image or "upload"
                _, dot, ext = url.rpartition('.')
                ext = f".{ext}" if dot else ""
                timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%S%fZ")
                unique_id = uuid.uuid4().hex
                file_name = f"{timestamp}_{unique_id}{ext}"

                folder_name = "stay_pics"
                stay_image_key = f"{folder_name}/{user_id}/{file_name}"

                self.s3_client.upload_file_from_url(folder_name, user_id, file_name, url)
                uploaded_file_names.append(stay_image_key)

                travel_stay = TravelStay.create(stay, saved_travel_log.id, user_id, stay_image_key)
                self.travel_stay_repo.create_travel_stay(travel_stay)

            return saved_travel_log
        
        except Exception as e:
            for file_name in uploaded_file_names:
                self.s3_client.delete_file(file_name);
            return None

    def get_travel_log_list_handler(self, user_id: int, theme: str | None = None):
        try:
            travel_logs = self.travel_log_repo.get_travel_log_by_user_id(user_id)

            # theme이 있는 경우 travel_logs를 미리 필터링
            if theme is not None:
                travel_logs = [
                    log for log in (travel_logs or [])
                    if log.theme == theme
                ]

            result = []

            for travel_log in travel_logs or []:
                image_urls = []
                for location in travel_log.locations or []:
                    s3_url = self.s3_client.get_file(location.image_link)
                    image_urls.append(s3_url)

                keywords = []
                for tag in travel_log.tags or []:
                    keywords.append(tag.tag)

                response_item = TravelLogListResponse(
                    travel_log_id=travel_log.id,
                    title=travel_log.title,
                    subtitle=travel_log.subtitle,
                    summary=travel_log.summary,
                    keywords=keywords,
                    images=image_urls
                )

                result.append(response_item)

            return result

        except Exception as e:
            print(e)

    def get_travel_log_handler(self, travel_log_id:int, user_id: int):
        travel_log = self.travel_log_repo.get_travel_log_by_log_id(travel_log_id)

        keywords = []
        for tag in travel_log.tags or []:
            keywords.append(tag.tag)

        grouped = defaultdict(list)

        for location in travel_log.locations or []:
            s3_url = self.s3_client.get_file(location.image_link)

            response = TravelLocationResponse(
                travel_location_id=location.id,
                title=location.title,
                longitude=location.longitude,
                latitude=location.latitude,
                location_type=location.location_type,
                description=location.description,
                travel_day=location.travel_day,
                image_link=s3_url
            )
            grouped[location.travel_day].append(response)

        response = TravelLogResponse(
            travel_log_id=travel_log.id,
            title=travel_log.title,
            subtitle=travel_log.subtitle,
            summary=travel_log.summary,
            keywords=keywords,
            locations=grouped,
        )

        return response


    def get_travel_log_map_handler(self, travel_log_id: int, user_id: int):
        try:
            travel_log = self.travel_log_repo.get_travel_log_by_log_id(travel_log_id)

            grouped = defaultdict(list)

            for location in travel_log.locations or []:
                response = TravelLocationMapResponse(
                    travel_location_id=location.id,
                    title=location.title,
                    longitude=location.longitude,
                    latitude=location.latitude,
                    location_type=location.location_type,
                    description=location.description,
                    image=location.image,
                )
                grouped[location.travel_day].append(response)

            response = TravelLogMapResponse(
                travel_log_id=travel_log.id,
                locations=grouped,
            )

            return response
        except Exception as e:
            print(e)