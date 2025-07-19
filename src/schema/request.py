from pydantic import BaseModel, EmailStr, Field

class KakaoLoginRequest(BaseModel):
    email: EmailStr = Field(..., description="User's email from Kakao")
    name: str = Field(..., description="User's name from Kakao")

class UserRegistrationRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="Unique username for the user")
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., min_length=6, description="User's password (minimum 6 characters)")

class LogoutRequest(BaseModel):
    refresh_token: str = Field(..., description="The refresh token to invalidate") 