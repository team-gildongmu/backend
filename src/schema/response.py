from pydantic import BaseModel

class KakaoLoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    user_id: int
    user_name: str
    is_new_user: bool


class UnlinkResponse(BaseModel):
    success: bool
    message: str

class RefreshTokenResponse(BaseModel):
    access_token: str
    email: str