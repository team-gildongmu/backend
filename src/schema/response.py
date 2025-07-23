from pydantic import BaseModel

class KakaoLoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    user_id: int

class UnlinkResponse(BaseModel):
    success: bool
    message: str