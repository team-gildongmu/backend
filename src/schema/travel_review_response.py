from typing import List

from pydantic import BaseModel

class TravelReviewCreateResponse(BaseModel):
    id: int

    class Config:
        from_attributes = True

class TravelReviewResponse(BaseModel):
    travel_review_id: int
    title: str
    ai_rating: float
    start_date: str
    end_date: str
    weather: str
    images: List[str]
    tags: List[str]
    mood: float
    note: str

    class Config:
        from_attributes = True

class TravelReviewListResponse(BaseModel):
    travel_review_id: int
    title: str
    ai_rating: float
    start_date: str
    end_date: str
    weather: str
    image: List[str]

    class Config:
        from_attributes = True

class TravelReviewCalendarResponse(BaseModel):
    travel_review_id: int
    title: str
    start_date: str
    end_date: str

    class Config:
        from_attributes = True