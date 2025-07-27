from sqlalchemy.orm import Session
from database.travel_orm import TravelLocation


class TravelLocationRepository:
    def __init__(self, session: Session):
        self.session = session

    def create_travel_locations(self, travel_locations: list[TravelLocation]) -> list[TravelLocation]:
        self.session.add_all(travel_locations)  # bulk insert
        self.session.flush()
        for loc in travel_locations:
            self.session.refresh(loc)
        return travel_locations
