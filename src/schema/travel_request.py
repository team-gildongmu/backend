from typing import List
from pydantic import BaseModel

class TravelLocationCreateRequest(BaseModel):
    name: str
    longitude: float
    latitude: float
    sequence: int
    congestion: str

class TravelLogCreateRequest(BaseModel):
    title: str
    locationCreateRequest: List[TravelLocationCreateRequest]