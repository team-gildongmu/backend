from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime


class StampResponse(BaseModel):
    id: int
    title: str
    is_stamped: bool = False
    stamped_at: Optional[datetime] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class CollectableStamp(BaseModel):
    id: int
    title: str
    distance_km: float
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class StampListResponse(BaseModel):
    stamps: List[StampResponse]


class CollectableStampResponse(BaseModel):
    stamps: List[CollectableStamp]
