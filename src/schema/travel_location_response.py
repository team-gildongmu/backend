from pydantic import BaseModel
from sqlalchemy.sql.sqltypes import Float


class TravelLocationResponse(BaseModel):
    travel_location_id: int
    title: str
    longitude: float
    latitude: float
    location_type: str
    description: str
    travel_day: int
    image_link: str

    class Config:
        from_attributes = True


class TravelLocationMapResponse(BaseModel):
    travel_location_id: int
    title: str
    longitude: float
    latitude: float
    location_type: str

    class Config:
        from_attributes = True
