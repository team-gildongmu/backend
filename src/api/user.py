from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.database.connection import get_db
from src.schema.request import KakaoLoginRequest
from src.schema.response import KakaoLoginResponse
from src.service.user_service import UserService
from pydantic import BaseModel, EmailStr, Field

router = APIRouter(prefix="/auth")

@router.post(
    "/kakao/login",
    response_model=KakaoLoginResponse,
    responses={
        200: {"description": "Successful login, returns JWT tokens"},
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
        user_service = UserService(db)
        result = user_service.authenticate_user(request.email, request.name)
        
        return KakaoLoginResponse(
            accessToken=result['access_token'], 
            refreshToken=result['refresh_token'], 
            userId=result['user'].id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error")


