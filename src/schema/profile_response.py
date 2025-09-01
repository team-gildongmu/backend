from pydantic import BaseModel

class ProfileResponse(BaseModel):
    nickname: str
    email: str
    intro: str
    profile_photo_url: str
