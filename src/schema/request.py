from pydantic import BaseModel, EmailStr, Field

class KakaoLoginRequest(BaseModel):
    code: str = Field(..., description="Authorization code from Kakao")

class KakaoUnlinkRequest(BaseModel):
    access_token: str = Field(..., description="Kakao access token to unlink") 