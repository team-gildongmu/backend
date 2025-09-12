from typing import List, Any, Sequence

from sqlalchemy import Row, RowMapping
from sqlalchemy.orm import Session
from sqlalchemy import select, delete

from database.travel_log_orm import TravelLog


class TravelLogRepository:
    def __init__(self, session: Session):
        self.session = session

    def create_travel_log(self, travelLog: TravelLog) -> TravelLog:
        try:
            self.session.add(instance=travelLog)
            self.session.flush()
            self.session.refresh(instance=travelLog) # db read
            return travelLog
        except Exception as e:
            print(f"Repository에서 에러: {e}")
            self.session.rollback()
            raise

    def get_travel_log_by_user_id(self, user_id: int) -> List[TravelLog]:
        return self.session.scalars(select(TravelLog).where(TravelLog.user_id == user_id)).unique().all()

    def get_travel_log_by_log_id(self, travel_log_id: int) -> TravelLog | None:
        return self.session.scalar(select(TravelLog).where(TravelLog.id == travel_log_id))