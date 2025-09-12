from sqlalchemy.orm import Session

from database.travel_location_orm import TravelLocation


class TravelLocationRepository:
    def __init__(self, session: Session):
        self.session = session

    def create_travel_location(self, travel_location: TravelLocation) -> TravelLocation:
        try:
            self.session.add(travel_location)  # 단일 insert
            self.session.flush()
            self.session.refresh(travel_location)
            return travel_location
        except Exception as e:
            print(f"Repository에서 에러: {e}")
            self.session.rollback()
            raise

    def create_travel_locations(self, travel_locations: list[TravelLocation]) -> list[TravelLocation]:
        self.session.add_all(travel_locations)  # bulk insert
        self.session.flush()
        for loc in travel_locations:
            self.session.refresh(loc)
        return travel_locations