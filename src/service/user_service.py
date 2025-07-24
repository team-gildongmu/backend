from sqlalchemy.orm import Session
from repository.user_repository import KakaoUserRepository
from utils.jwt_utils import create_access_token, create_refresh_token
from utils.kakao_client import KakaoClient
from typing import Dict
import os

class KakaoUserService:
    def __init__(self, db: Session):
        self.user_repository = KakaoUserRepository(db)
        self.kakao_client = KakaoClient(
            client_id=os.getenv("KAKAO_CLIENT_ID"),
            redirect_uri=os.getenv("KAKAO_REDIRECT_URI", "http://localhost:3000/oauth/kakao")
        )
    
    def authenticate_with_kakao(self, code: str) -> Dict:
        """Authenticate user with Kakao authorization code"""
        # Exchange code for Kakao tokens
        kakao_token_info = self.kakao_client.get_token(code)
        
        # Get user info from Kakao
        user_info = self.kakao_client.get_user_info(kakao_token_info['access_token'])
        
        # Extract user details from Kakao response
        kakao_account = user_info.get('kakao_account', {})
        
        # Get email from kakao_account
        email = kakao_account.get('email')
        if not email:
            raise ValueError("Email not provided by Kakao")
        
        # Get profile info - first try kakao_account.profile, then properties
        profile = kakao_account.get('profile', {}) or user_info.get('properties', {})
        
        # Get name/nickname - try multiple possible locations
        name = (profile.get('nickname') or 
                user_info.get('properties', {}).get('nickname') or 
                'Unknown')
        
        # Get profile photo - try multiple possible locations
        profile_photo = (profile.get('profile_image_url') or 
                        profile.get('profile_image') or 
                        None)
        
        # Ensure values are strings
        name = str(name) if name else 'Unknown'
        profile_photo = str(profile_photo) if profile_photo else None
        
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
            # Re-raise the exception to be handled by the API layer
            raise e 