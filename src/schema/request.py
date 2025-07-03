from pydantic import BaseModel, EmailStr, Field

class KakaoLoginRequest(BaseModel):
    email: EmailStr = Field(..., description="User's email from Kakao")
    name: str = Field(..., description="User's name from Kakao") 