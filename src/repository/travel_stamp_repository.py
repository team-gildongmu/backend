from database.travel_orm import TravelStamp
from typing import List 
from datetime import datetime



class TravelStampRepository:
    def __init__(self, session):
        self.session = session

    def create_travel_stamps(self, travel_stamps: list[TravelStamp]) -> list[TravelStamp]:
        self.session.add_all(travel_stamps)
        self.session.flush()
        for stamp in travel_stamps:
            self.session.refresh(stamp)
        return travel_stamps

    def find_by_user(self, user_id: int) -> List[TravelStamp]:
        return self.session.query(TravelStamp).filter(
            TravelStamp.user_id == user_id
        ).all()

    def update_stamp_completed(
        self, 
        user_id: int, 
        stamp_id: int, 
        stamped_at: datetime | None = None
    ) -> TravelStamp:
        stamp = self.session.query(TravelStamp).filter(
            TravelStamp.id == stamp_id,
            TravelStamp.user_id == user_id
        ).first()

        if not stamp:
            raise ValueError("Stamp not found or does not belong to this user")

        stamp.is_stamped = True
        stamp.stamped_at = stamped_at or datetime.utcnow()
        self.session.commit()
        self.session.refresh(stamp)  # refresh to get updated fields
        return stamp
