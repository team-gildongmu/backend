from sqlalchemy.orm import Session
from repository.user_repository import UserRepository
from utils.jwt_utils import create_access_token, create_refresh_token
from utils.kakao_client import KakaoClient
import os
import logging
from typing import Dict

logger = logging.getLogger(__name__)

class UserService:
    def __init__(self, db: Session):
        self.user_repository = UserRepository(db)
        # Initialize KakaoClient with environment variables
        client_id = os.getenv("KAKAO_CLIENT_ID")
        client_secret = os.getenv("KAKAO_CLIENT_SECRET")
        redirect_uri = os.getenv("KAKAO_REDIRECT_URI")
        self.kakao_client = KakaoClient(client_id, client_secret, redirect_uri)

    def authenticate_with_kakao(self, authorization_code: str):
        """Complete Kakao OAuth flow and return user with tokens"""
        try:

            kakao_access_token = self.kakao_client._get_kakao_access_token(authorization_code)
            kakao_profile = self.kakao_client._get_kakao_user_profile(kakao_access_token)
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
    
    def unlink_kakao(self, access_token: str) -> Dict:
        """Unlink user from Kakao"""
        try:
            result = self.kakao_client.unlink(access_token)
            return {
                "success": True,
                "message": f"Successfully unlinked Kakao user ID: {result.get('id')}"
            }
        except Exception as e:
            # Re-raise the exception to be handled by the API layer
            raise e 

