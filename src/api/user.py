from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from database.connection import get_db
from schema.request import KakaoLoginRequest, KakaoUnlinkRequest
from schema.response import KakaoLoginResponse, UnlinkResponse
from service.user_service import KakaoUserService
import os
import json
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth")


#handled in FE
# @router.get("/kakao/login-url")
# def get_kakao_login_url():
#     """Get Kakao login URL"""
#     client_id = os.getenv("KAKAO_CLIENT_ID")
#     redirect_uri = os.getenv("KAKAO_REDIRECT_URI", "http://localhost:3000/oauth/kakao")
#     return {
#         "login_url": f"https://kauth.kakao.com/oauth/authorize?client_id={client_id}&redirect_uri={redirect_uri}&response_type=code"
#     }

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
        user_service = KakaoUserService(db)
        
        try:
            result = user_service.authenticate_with_kakao(request.code)
            return KakaoLoginResponse(
                access_token=result['access_token'],
                refresh_token=result['refresh_token'],
                user_id=result['user'].id,

            )
        except Exception as service_error:
            logger.error(f"Error in KakaoUserService: {str(service_error)}")
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

@router.post(
    "/kakao/unlink",
    response_model=UnlinkResponse,
    responses={
        200: {"description": "Successfully unlinked from Kakao"},
        400: {"description": "Bad request - invalid token"},
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
        # Log the error for debugging
        logger.error(f"Error unlinking from Kakao: {str(e)}")
        
        # Check if it's a 4xx error (client error) or 5xx error (server error)
        if hasattr(e, 'response') and hasattr(e.response, 'status_code'):
            if e.response.status_code >= 400 and e.response.status_code < 500:
                raise HTTPException(status_code=400, detail=f"Failed to unlink: {str(e)}")
            else:
                raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
        else:
            # Default to 500 for unexpected errors
            raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")




