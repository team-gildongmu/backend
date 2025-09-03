from pydantic import BaseModel
from typing import Optional

class ProfileResponse(BaseModel):
    nickname: str
    email: str
    intro: Optional[str]
    profile_photo_url: Optional[str]
