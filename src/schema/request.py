from pydantic import BaseModel, EmailStr

class KakaoLoginRequest(BaseModel):
    email: EmailStr
    name: str 