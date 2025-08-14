from sqlalchemy.orm import Session
from repository.user_repository import UserRepository
from repository.refresh_token_repository import RefreshTokenRepository
from utils.jwt_utils import create_access_token, create_refresh_token, decode_token
from utils.kakao_client import KakaoClient
import os
import logging
from typing import Dict

logger = logging.getLogger(__name__)

class UserService:
    def __init__(self, db: Session):
        self.user_repository = UserRepository(db)
        self.refresh_token_repository = RefreshTokenRepository(db)
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
            # persist refresh token
            self.refresh_token_repository.save(user.id, refresh_token)
            
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

    def refresh_access_token(self, raw_refresh_token: str) -> Dict:
        """Validate refresh token: verify it exists in DB, then issue a new access token."""
        payload = decode_token(raw_refresh_token)
        if not payload:
            raise ValueError("Invalid or expired refresh token")

       
        token_row = self.refresh_token_repository.find_by_token(raw_refresh_token)
        if token_row is None:
            raise ValueError("Refresh token not recognized")

        email = payload.get("email")
        user = self.user_repository.find_by_email(email)
        if not user:
            raise ValueError("User does not exist")

        new_access_token = create_access_token(user.id, user.email)
        return {"access_token": new_access_token, "email": user.email}

    def revoke_refresh_token(self, raw_refresh_token: str) -> None:
        # Best-effort delete; do not reveal whether token existed
        self.refresh_token_repository.delete_by_token(raw_refresh_token)

    def revoke_all_refresh_tokens_for_user(self, user_id: int) -> None:
        self.refresh_token_repository.delete_all_for_user(user_id)

    def rotate_refresh_token(self, old_refresh_token: str) -> Dict:
        payload = decode_token(old_refresh_token)
        if not payload:
            raise ValueError("Invalid or expired refresh token")

        # verify old token still stored
        token_row = self.refresh_token_repository.find_by_token(old_refresh_token)
        if token_row is None:
            raise ValueError("Refresh token not recognized")

        email = payload.get("email")
        user = self.user_repository.find_by_email(email)
        if not user or user.id != token_row.user_id:
            self.revoke_refresh_token(old_refresh_token)
            raise ValueError("User does not exist or token ownership mismatch")

        # revoke old and issue new
        self.refresh_token_repository.delete_by_token(old_refresh_token)
        new_refresh = create_refresh_token(user.id, user.email)
        self.refresh_token_repository.save(user.id, new_refresh)

        # optionally issue a new access token alongside rotation
        new_access = create_access_token(user.id, user.email)
        return {"access_token": new_access, "refresh_token": new_refresh, "email": user.email}

