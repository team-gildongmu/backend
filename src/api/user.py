from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.connection import get_db, engine
from schema.request import KakaoLoginRequest
from schema.response import KakaoLoginResponse
from service.user import get_or_create_user
from service.jwt_utils import create_access_token, create_refresh_token
from pydantic import BaseModel, EmailStr, Field
from database.orm import Base

router = APIRouter(prefix="/auth")

@router.post(
    "/kakao/login",
    response_model=KakaoLoginResponse,
    responses={
        200: {"description": "Successful login, returns JWT tokens"}, #! TO-DO  - 다른 코드..?
        500: {"description": "Internal server error"}
    }
)
def kakao_login(request: KakaoLoginRequest, db: Session = Depends(get_db)):
    """
    Kakao social login endpoint.

    - **email**: User's email from Kakao
    - **name**: User's name from Kakao

    Returns access and refresh JWT tokens.
    """
    try:
        user = get_or_create_user(db, request.email, request.name)
        access_token = create_access_token(user.id, user.email)
        refresh_token = create_refresh_token(user.id, user.email)
        print(user.id)
        print(refresh_token)
        print(access_token)
        return KakaoLoginResponse(accessToken=access_token, refreshToken=refresh_token, userId=user.id)
    except Exception as e:
        print(f"Error in kakao_login: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

class KakaoLoginRequest(BaseModel):
    email: EmailStr = Field(..., description="User's email from Kakao")
    name: str = Field(..., description="User's name from Kakao") 