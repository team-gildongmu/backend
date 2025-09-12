from database.travel_log_tag_orm import TravelLogTag


class TravelLogTagRepository:
    def __init__(self, session):
        self.session = session

    def create_travel_log_tags(self, travel_log_tags: list[TravelLogTag]) -> list[TravelLogTag]:
        self.session.add_all(travel_log_tags)  # bulk insert
        self.session.flush()
        for tag in travel_log_tags:
            self.session.refresh(tag)
        return travel_log_tags