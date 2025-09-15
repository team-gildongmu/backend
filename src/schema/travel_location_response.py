from pydantic import BaseModel

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
    description: str
    image: str

    class Config:
        from_attributes = True
