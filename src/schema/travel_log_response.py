from typing import List, Dict

from pydantic import BaseModel

from database.travel_location_orm import TravelLocation
from schema.travel_location_response import TravelLocationResponse, TravelLocationMapResponse


class TravelLogCreateResponse(BaseModel):
    id: int

    class Config:
        from_attributes = True

class TravelLogListResponse(BaseModel):
    travel_log_id: int
    title: str
    subtitle: str
    summary: str
    keywords: List[str]
    images: List[str]

    class Config:
        from_attributes = True

class TravelLogResponse(BaseModel):
    travel_log_id: int
    title: str
    subtitle: str
    summary: str
    keywords: List[str]
    locations: Dict[int, List[TravelLocationResponse]]

    class Config:
        from_attributes = True

class TravelLogMapResponse(BaseModel):
    travel_log_id: int
    locations: Dict[int, List[TravelLocationMapResponse]]

    class Config:
        from_attributes = True