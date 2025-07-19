from pydantic import BaseModel

class KakaoLoginResponse(BaseModel):
    accessToken: str
    refreshToken: str 
    userId: int


#tokens response
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenWithRefresh(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None