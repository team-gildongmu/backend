from pydantic import BaseModel

class ProfileResponse(BaseModel):
    nickname: str
    email: str
    intro: Optional[str]
    profile_photo_url: Optional[str]
