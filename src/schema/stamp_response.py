from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime


class StampResponse(BaseModel):
    id: int
    title: str
    is_stamped: bool
    stamped_at: Optional[datetime] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class StampListResponse(BaseModel):
    stamps: List[StampResponse]
