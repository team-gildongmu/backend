from pydantic import BaseModel

class TravelLogCreateResponse(BaseModel):
    id: int

    class Config:
        from_attributes = True