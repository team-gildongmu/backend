from sqlalchemy.orm.session import Session

from database.travel_orm import TravelLog, TravelLocation, TravelStamp
from repository.travel_location_repository import TravelLocationRepository
from repository.travel_log_repository import TravelLogRepository
from repository.travel_stamp_repository import TravelStampRepository
from schema.travel_request import TravelLogCreateRequest


class TravelLogService:
    def __init__(self, session: Session):
        self.session = session
        self.travel_log_repo = TravelLogRepository(session)
        self.travel_location_repo = TravelLocationRepository(session)
        self.travel_stamp_repo = TravelStampRepository(session)

    def create_travel_log(self, request: TravelLogCreateRequest):
        try:
            with self.session.begin():
                travel_log = TravelLog.create(request)
                saved_travel_log = self.travel_log_repo.create_travel_log(travel_log)
                print(f"Travel log created: {saved_travel_log.id}")

                travel_locations = [
                    TravelLocation.create(loc_req, saved_travel_log)
                    for loc_req in request.locationCreateRequest
                ]
                saved_travel_locations = self.travel_location_repo.create_travel_locations(travel_locations)
                print(f"Travel locations created: {len(saved_travel_locations)}")

                travel_stamps = TravelStamp.create_stamps(saved_travel_log, saved_travel_locations)
                self.travel_stamp_repo.create_travel_stamps(travel_stamps)
                print("Travel stamps created successfully")

                return saved_travel_log

        except Exception as e:
            print(f"Error in create_travel_log: {e}")
            print(f"Error type: {type(e)}")
            import traceback
            traceback.print_exc()
            raise
