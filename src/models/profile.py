from dataclasses import dataclass
from typing import Optional

@dataclass
class ProfileData:
    nickname: str
    email: str
    intro: Optional[str]
    profile_photo_key: Optional[str]