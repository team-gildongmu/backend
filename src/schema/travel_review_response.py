from pydantic import BaseModel

class TravelReviewCreateResponse(BaseModel):
    id: int

    class Config:
        from_attributes = True