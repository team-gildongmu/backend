from sqlalchemy.orm import Session
from database.travel_orm import TravelLog


class TravelLogRepository:
    def __init__(self, session: Session):
        self.session = session

    def create_travel_log(self, travelLog: TravelLog) -> TravelLog:
        self.session.add(instance=travelLog)
        self.session.flush()
        self.session.refresh(instance=travelLog) # db read
        return travelLog
