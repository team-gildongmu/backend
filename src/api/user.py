from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.connection import get_db
from schema.request import KakaoLoginRequest, KakaoUnlinkRequest
from schema.response import KakaoLoginResponse, UnlinkResponse
from service.user_service import KakaoUserService
import os

router = APIRouter(prefix="/auth")

@router.get("/kakao/login-url")
def get_kakao_login_url():
    """Get Kakao login URL"""
    client_id = os.getenv("KAKAO_CLIENT_ID")
    redirect_uri = os.getenv("KAKAO_REDIRECT_URI")
    return {
        "login_url": f"https://kauth.kakao.com/oauth/authorize?client_id={client_id}&redirect_uri={redirect_uri}&response_type=code"
    }

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
    
    Returns access and refresh JWT tokens along with Kakao tokens.
    """
    try:
        kakao_user_service = KakaoUserService(db)
        result = kakao_user_service.authenticate_with_kakao(request.code)
        
        return KakaoLoginResponse(
            access_token=result['access_token'],
            refresh_token=result['refresh_token'],
            user_id=result['user'].id,
            kakao_access_token=result['kakao_access_token'],
            kakao_refresh_token=result['kakao_refresh_token'],
            kakao_token_expires_in=result['kakao_token_expires_in']
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.post(
    "/kakao/unlink",
    response_model=UnlinkResponse,
    responses={
        200: {"description": "Successfully unlinked from Kakao"},
        500: {"description": "Internal server error"}
    }
)
def kakao_unlink(request: KakaoUnlinkRequest, db: Session = Depends(get_db)):
    """
    Unlink user from Kakao.
    
    - **access_token**: Kakao access token to unlink
    """
    try:
        user_service = KakaoUserService(db)
        result = user_service.unlink_kakao(request.access_token)
        return UnlinkResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error")


