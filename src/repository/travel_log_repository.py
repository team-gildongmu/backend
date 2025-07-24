from fastapi import Depends
from sqlalchemy.orm import Session
from database.connection import get_db
from database.orm import TravelLog


class TravelLogRepository:
    def __init__(self, session: Session =  Depends(get_db)):
        self.session = session

    def create_travel_log(self, travelLog: TravelLog) -> TravelLog:
        self.session.add(instance=travelLog)
        self.session.flush()
        self.session.refresh(instance=travelLog) # db read
        return travelLog
