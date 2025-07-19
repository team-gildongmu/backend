from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.connection import get_db
from schema.request import KakaoLoginRequest
from schema.response import KakaoLoginResponse, TokenWithRefresh
from service.user_service import UserService, KakaoUserService
from service.token_service import TokenService
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from schema.response import Token

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
        user_service = KakaoUserService(db)
        result = user_service.authenticate_user(request.email, request.name)
        
        return KakaoLoginResponse(
            accessToken=result['access_token'], 
            refreshToken=result['refresh_token'], 
            userId=result['user'].id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.post("/login", response_model=TokenWithRefresh)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(get_db)
) -> TokenWithRefresh:

    user_service = UserService(db)
    
    user = user_service.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create tokens and save refresh token to database
    tokens = user_service.create_tokens_for_user(user)
    
    return TokenWithRefresh(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        token_type="bearer"
    )


@router.post("/logout")
async def logout(refresh_token: str, db: Session = Depends(get_db)):
    """
    Logout endpoint to invalidate refresh token.
    
    - **refresh_token**: The refresh token to invalidate
    """
    user_service = UserService(db)
    
    # Delete refresh token from the single table
    user_service.user_repository.delete_refresh_token(refresh_token)
    
    return {"message": "Successfully logged out"}


