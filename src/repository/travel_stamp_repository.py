from database.travel_orm import TravelStamp


class TravelStampRepository:
    def __init__(self, session):
        self.session = session

    def create_travel_stamp(self, travel_stamp: TravelStamp) -> TravelStamp:
        self.session.add(travel_stamp)
        self.session.flush()
        self.session.refresh(travel_stamp)
        return travel_stamp

    def create_travel_stamps(self, travel_stamps: list[TravelStamp]) -> list[TravelStamp]:
        self.session.add_all(travel_stamps)
        self.session.flush()
        for stamp in travel_stamps:
            self.session.refresh(stamp)
        return travel_stamps
