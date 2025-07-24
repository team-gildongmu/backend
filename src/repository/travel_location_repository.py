from fastapi import Depends
from sqlalchemy.orm import Session
from database.connection import get_db
from database.orm import TravelLog, TravelLocation


class TravelLocationRepository:
    def __init__(self, session: Session =  Depends(get_db)):
        self.session = session

    def create_travel_locations(self, travel_locations: list[TravelLocation]) -> list[TravelLocation]:
        self.session.add_all(travel_locations)  # bulk insert
        self.session.flush()
        for loc in travel_locations:
            self.session.refresh(loc)
        return travel_locations
