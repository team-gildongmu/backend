from pydantic import BaseModel

class KakaoLoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    user_id: int
    kakao_access_token: str
    kakao_refresh_token: str
    kakao_token_expires_in: int

class UnlinkResponse(BaseModel):
    success: bool
    message: str