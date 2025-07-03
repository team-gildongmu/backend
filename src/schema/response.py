from pydantic import BaseModel

class KakaoLoginResponse(BaseModel):
    accessToken: str
    refreshToken: str 
    userId: int