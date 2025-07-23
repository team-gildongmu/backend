from sqlalchemy.orm import Session
from repository.user_repository import UserRepository
from utils.jwt_utils import create_access_token, create_refresh_token
from utils.kakao_client import KakaoClient
from typing import Dict
import os

class KakaoUserService:
    def __init__(self, db: Session):
        self.user_repository = UserRepository(db)
        self.kakao_client = KakaoClient(
            client_id=os.getenv("KAKAO_CLIENT_ID"),
            client_secret=os.getenv("KAKAO_CLIENT_SECRET"),
            redirect_uri=os.getenv("KAKAO_REDIRECT_URI")
        )
    
    def authenticate_with_kakao(self, code: str) -> Dict:
        """Authenticate user with Kakao authorization code"""
        # Exchange code for Kakao tokens
        kakao_token_info = self.kakao_client.get_token(code)
        
        # Get user info from Kakao
        user_info = self.kakao_client.get_user_info(kakao_token_info['access_token'])
        
        # Extract user details from Kakao response
        kakao_account = user_info.get('kakao_account', {})
        profile = kakao_account.get('profile', {})
        
        email = kakao_account.get('email')
        if not email:
            raise ValueError("Email not provided by Kakao")
            
        name = profile.get('nickname', 'Unknown')
        profile_photo = profile.get('profile_image_url')
        
        # Get or create user
        user = self.user_repository.get_or_create_user(
            email=email,
            name=name,
            profile_photo=profile_photo
        )
        
        # Generate our JWT tokens
        access_token = create_access_token(user.id, user.email)
        refresh_token = create_refresh_token(user.id, user.email)
        
        return {
            "user": user,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "kakao_access_token": kakao_token_info['access_token'],
            "kakao_refresh_token": kakao_token_info.get('refresh_token'),
            "kakao_token_expires_in": kakao_token_info.get('expires_in')
        }
    
    def unlink_kakao(self, access_token: str) -> Dict:
        """Unlink user from Kakao"""
        try:
            result = self.kakao_client.unlink(access_token)
            return {
                "success": True,
                "message": f"Successfully unlinked Kakao user ID: {result.get('id')}"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to unlink: {str(e)}"
            } 