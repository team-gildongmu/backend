from sqlalchemy.orm import Session
from repository.user_repository import UserRepository
from utils.jwt_utils import create_access_token, create_refresh_token
import requests
import os
import logging

logger = logging.getLogger(__name__)

class UserService:
    def __init__(self, db: Session):
        self.user_repository = UserRepository(db)

    def authenticate_with_kakao(self, authorization_code: str):
        """Complete Kakao OAuth flow and return user with tokens"""
        try:

            kakao_access_token = self._get_kakao_access_token(authorization_code)
            kakao_profile = self._get_kakao_user_profile(kakao_access_token)
            user, is_new_user = self.user_repository.get_or_create_kakao_user(kakao_profile)
            access_token = create_access_token(user.id, user.email)
            refresh_token = create_refresh_token(user.id, user.email)
            
            logger.info(f"User {'created' if is_new_user else 'authenticated'}: {user.username} ({user.email})")
      
            return {
                "user_id": user.id,
                "user_name": user.username,
                "access_token": access_token,
                "refresh_token": refresh_token,
                "is_new_user": is_new_user
            }
            
        except Exception as e:
            logger.error(f"Kakao authentication failed: {str(e)}")
            raise e
    
    def _get_kakao_access_token(self, authorization_code: str) -> str:
        """Exchange authorization code for Kakao access token"""
        client_id = os.getenv("KAKAO_CLIENT_ID")
        client_secret = os.getenv("KAKAO_CLIENT_SECRET")
        redirect_uri = os.getenv("KAKAO_REDIRECT_URI")
        
        token_url = "https://kauth.kakao.com/oauth/token"
        data = {
            "grant_type": "authorization_code",
            "client_id": client_id,
            "client_secret": client_secret,
            "code": authorization_code,
            "redirect_uri": redirect_uri
        }
        
        response = requests.post(token_url, data=data)
        response.raise_for_status()
        token_data = response.json()
        return token_data["access_token"]
    
    def _get_kakao_user_profile(self, access_token: str) -> dict:
        """Get user profile from Kakao API"""
        headers = {"Authorization": f"Bearer {access_token}"}
        profile_url = "https://kapi.kakao.com/v2/user/me"
        
        response = requests.get(profile_url, headers=headers)
        response.raise_for_status()
        return response.json() 