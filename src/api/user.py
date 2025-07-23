from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.connection import get_db
from schema.request import KakaoLoginRequest, KakaoLoginEmailRequest
from schema.response import KakaoLoginResponse
from service.user_service import UserService
from pydantic import BaseModel, EmailStr, Field
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth")

@router.post(
    "/kakao/callback",
    response_model=KakaoLoginResponse,
    responses={
        200: {"description": "Successful login, returns JWT tokens"},
        400: {"description": "Invalid request"},
        500: {"description": "Internal server error"}
    }
)
def kakao_callback(request: KakaoLoginRequest, db: Session = Depends(get_db)):
    """
    Handle Kakao OAuth callback.
    
    - **code**: Authorization code from Kakao
    
    Returns access and refresh JWT tokens.
    """
    try:
        user_service = UserService(db)
        result = user_service.authenticate_with_kakao(request.code)
        
        return KakaoLoginResponse(
            accessToken=result['access_token'],
            refreshToken=result['refresh_token'],
            userId=result['user'].id
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error in Kakao authentication: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.post(
    "/kakao/login",
    response_model=KakaoLoginResponse,
    responses={
        200: {"description": "Successful login, returns JWT tokens"},
        500: {"description": "Internal server error"}
    }
)
def kakao_login(request: KakaoLoginEmailRequest, db: Session = Depends(get_db)):
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


