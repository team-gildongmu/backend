from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from database.connection import get_db
from schema.request import KakaoLoginRequest, KakaoUnlinkRequest
from schema.response import KakaoLoginResponse, UnlinkResponse, RefreshTokenResponse
from service.user_service import UserService
import os
import json
import logging
from utils.jwt_utils import decode_token, create_access_token
from utils.auth_util import get_refresh_token_from_cookie, JWTBearer


# Set up logging
logging.basicConfig(level=logging.INFO)
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
async def kakao_callback(request: KakaoLoginRequest, db: Session = Depends(get_db)):
    """
    Handle Kakao OAuth callback.
    """
    try:
        # Log the received code
        logger.info(f"Received authorization code: {request.code[:10]}...")
        
        # Check if we have the required environment variables
        client_id = os.getenv("KAKAO_CLIENT_ID")
        if not client_id:
            logger.error("Missing KAKAO_CLIENT_ID environment variable")
            raise HTTPException(
                status_code=500,
                detail="Server configuration error: Missing KAKAO_CLIENT_ID"
            )
            
        # Initialize service
        user_service = UserService(db)
        
        try:
            result = user_service.authenticate_with_kakao(request.code)
            
            # Check if all required fields are present
            if not result or 'access_token' not in result or 'refresh_token' not in result:
                print("Missing required fields in result")
                raise HTTPException(status_code=500, detail="Service returned incomplete data")
            
            return KakaoLoginResponse(
                access_token=result['access_token'],
                refresh_token=result['refresh_token'],
                user_id=result['user_id'],
                user_name=result['user_name'],
                is_new_user=result['is_new_user']
            )
        except Exception as service_error:
            logger.error(f"Error in UserService: {str(service_error)}")
            raise HTTPException(
                status_code=400,
                detail=f"Authentication failed: {str(service_error)}"
            )
            
    except HTTPException as http_error:
        # Re-raise HTTP exceptions
        raise http_error
    except Exception as e:
        logger.error(f"Unexpected error in callback: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal Server Error: {str(e)}"
        )


    
@router.post("/refresh", response_model=RefreshTokenResponse)
async def refresh_token(refresh_token: str = Depends(get_refresh_token_from_cookie), db: Session = Depends(get_db)):
    if not refresh_token:
        raise HTTPException(status_code=401, detail="No refresh token")

    user_service = UserService(db)
    try:
        result = user_service.refresh_access_token(refresh_token)
        return RefreshTokenResponse(access_token=result["access_token"], email=result["email"])
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))



@router.post(
    "/logout",
    responses={
        200: {"description": "Successfully logged out"},
        401: {"description": "Unauthorized - no valid session"},
        500: {"description": "Internal server error"}
    }
)
async def logout(
    response: Response,
    db: Session = Depends(get_db),
    refresh_token: str = Depends(get_refresh_token_from_cookie)
):
    """
    Logout user by deleting refresh token from DB.
    """
    try:
        if not refresh_token:
            raise HTTPException(status_code=401, detail="No refresh token")
        user_service = UserService(db)
        user_service.invalidate_refresh_token(refresh_token) 
        response.delete_cookie(key="refresh-token")
        return {"message": "Successfully logged out"}
    except Exception as e:
        logger.error(f"Error logging out: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")




