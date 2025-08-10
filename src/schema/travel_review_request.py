from pydantic import BaseModel

class TravelReviewCreateRequest(BaseModel):
    travel_log_id: int
    title: str
    ai_rating: float
    started_at: str
    finished_at: str
    weather: str
    mood: str
    tag: str
    note: str
    song: str
