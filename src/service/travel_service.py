import json
import uuid
from datetime import datetime

from sqlalchemy.orm.session import Session
from datetime import datetime
from typing import List
from database.travel_location_orm import TravelLocation
from database.travel_orm import TravelLog, TravelStamp, TravelLogTag
from database.travel_stay_orm import TravelStay
from repository.travel_location_repository import TravelLocationRepository
from repository.travel_log_repository import TravelLogRepository
from repository.travel_log_tag_repository import TravelLogTagRepository
from repository.travel_stamp_repository import TravelStampRepository
from repository.travel_stay_repository import TravelStayRepository
from schema.travel_request import TravelLogCreateRequest
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


    def get_travel_stamps(self, user_id: int) -> List[TravelStamp]:
        return self.travel_stamp_repo.find_by_user(user_id)

    def update_stamp_completed(self, user_id: int, stamp_id: int, stamped_at: datetime | None = None) -> TravelStamp:
        try:
            return self.travel_stamp_repo.update_stamp_completed(user_id, stamp_id, stamped_at)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))