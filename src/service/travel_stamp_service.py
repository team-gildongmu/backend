import uuid
import os

from sqlalchemy.orm.session import Session
from datetime import datetime
from typing import List
from database.travel_orm import TravelLog, TravelStamp, TravelLogTag
from repository.travel_stamp_repository import TravelStampRepository
from utils.calc_utils import haversine
from schema.stamp_response import CollectableStamp


class TravelStampService:
    def __init__(self, session: Session):
        self.session = session
        self.travel_stamp_repo = TravelStampRepository(session)
        self.radius_km = float(os.getenv("STAMP_RADIUS_KM", 2))

    def get_travel_stamps(self, user_id: int) -> List[TravelStamp]:
        return self.travel_stamp_repo.find_by_user(user_id)

    def update_stamp_completed(self, user_id: int, stamp_id: int, stamped_at: datetime | None = None) -> TravelStamp:
        try:
            return self.travel_stamp_repo.update_stamp_completed(user_id, stamp_id, stamped_at)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))

    def get_collectable_stamps(self, user_id: int, user_lat: float, user_lon: float) -> List[CollectableStamp]:
        stamps = self.travel_stamp_repo.find_unstamped_by_user(user_id)

        nearby_stamps: List[CollectableStamp] = []
        for stamp in stamps:
            loc = stamp.location
            if loc and loc.latitude and loc.longitude:
                dist = haversine(user_lat, user_lon, loc.latitude, loc.longitude)
                if dist <= self.radius_km:
                    nearby_stamps.append(
                        CollectableStamp(
                            id=stamp.id,
                            title=loc.title,
                            latitude=loc.latitude,
                            longitude=loc.longitude,
                            distance_km=round(dist, 2)
                        )
                    )

        return nearby_stamps