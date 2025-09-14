from database.travel_stay_orm import TravelStay


class TravelStayRepository:
    def __init__(self, session):
        self.session = session

    def create_travel_stay(self, travel_stay: TravelStay) -> TravelStay:
        try:
            self.session.add(travel_stay)
            self.session.flush()
            self.session.refresh(travel_stay)
            return travel_stay
        except Exception as e:
            print(f"Repository에서 에러: {e}")
            self.session.rollback()
            raise
