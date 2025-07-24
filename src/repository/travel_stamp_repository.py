from database.travel_orm import TravelStamp


class TravelStampRepository:
    def __init__(self, session):
        self.session = session

    def create_travel_stamps(self, travel_stamps: list[TravelStamp]) -> list[TravelStamp]:
        self.session.add_all(travel_stamps)
        self.session.flush()
        for stamp in travel_stamps:
            self.session.refresh(stamp)
        return travel_stamps
