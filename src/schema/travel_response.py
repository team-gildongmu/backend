from typing import List

from pydantic import BaseModel

class TravelLogCreateResponse(BaseModel):
    id: int

    class Config:
        from_attributes = True

class TravelLogListResponse(BaseModel):
    travel_log_id: int
    title: str
    summary: str
    keywords: List[str]
    images: List[str]

    class Config:
        from_attributes = True