from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from database.connection import get_db
from schema.request import KakaoLoginRequest, KakaoUnlinkRequest
from schema.response import KakaoLoginResponse, UnlinkResponse
from service.user_service import UserService
import os
import json
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
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
        user_service = UserService(db)
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


"""
아래 코드는 카카오 로그인 테스트 용으로 사용하는 코드입니다.
실제 로그인 시 사용하지 않습니다. (프론트 쪽에서 처리)
"""
# @router.post("/kakao/get-real-code")
# async def get_real_kakao_authorization_code(request: dict, db: Session = Depends(get_db)):
#     """
#     Get REAL Kakao authorization code using email and password.
#     This calls the actual Kakao API.
#     """
#     try:
#         email = request.get("email")
#         password = request.get("password")
        
#         if not email or not password:
#             raise HTTPException(status_code=400, detail="Email and password are required")
        
#         logger.info(f"Attempting to get real Kakao authorization code for: {email}")
        
#         # Call Kakao's login API to get authorization code
#         # This is the real Kakao authentication flow
#         import requests
        
#         # Kakao login endpoint
#         login_url = "https://accounts.kakao.com/login"
        
#         # Create session to maintain cookies
#         session = requests.Session()
        
#         # First, get the login page to get any required tokens
#         login_page_response = session.get(login_url)
        
#         # Now attempt to login with credentials
#         login_data = {
#             "email": email,
#             "password": password,
#             "continue": "https://kauth.kakao.com/oauth/authorize"
#         }
        
#         login_response = session.post(login_url, data=login_data)
        
#         # Check if login was successful
#         if login_response.status_code == 200 and "authorization_code" in login_response.text:
#             # Extract authorization code from response
#             import re
#             code_match = re.search(r'authorization_code=([a-zA-Z0-9]+)', login_response.text)
#             if code_match:
#                 authorization_code = code_match.group(1)
                
#                 return {
#                     "authorization_code": authorization_code,
#                     "email": email,
#                     "name": email.split("@")[0],
#                     "message": "Real authorization code obtained from Kakao"
#                 }
        
#         # If we get here, login failed
#         raise HTTPException(status_code=401, detail="Invalid Kakao credentials")
        
#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"Error getting real Kakao authorization code: {str(e)}")
#         raise HTTPException(status_code=500, detail=f"Failed to get authorization code: {str(e)}")




