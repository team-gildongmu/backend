from sqlalchemy.orm import Session
from repository.user_repository import UserRepository
from utils.jwt_utils import create_access_token, create_refresh_token
from utils.hash_password import verify_password
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from jwt.exceptions import InvalidTokenError
from passlib.context import CryptContext
from utils.tokens import oauth2_scheme
from utils.tokens import SECRET_KEY, ALGORITHM
from schema.response import TokenData

class UserService:
    def __init__(self, db: Session):
        self.user_repository = UserRepository(db)
    
    def authenticate_user(self, email: str, password: str):
        """Authenticate user with email and password"""
        user = self.user_repository.get_user_by_email(email)
        if not user:
            return False
        if not verify_password(password, user.hashed_password):
            return False
        return user
    
    def create_tokens_for_user(self, user):
        """Create access and refresh tokens for user and save refresh token"""
        
        access_token = create_access_token(user.id, user.email)
        refresh_token = create_refresh_token(user.id, user.email)
        
        # Save refresh token linked by email
        self.user_repository.save_refresh_token(user.email, refresh_token)
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token
        }
    
    async def get_current_user(self, token: Annotated[str, Depends(oauth2_scheme)]):
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            email = payload.get("sub")
            if email is None:
                raise credentials_exception
            token_data = TokenData(username=email)  # Using email as username in token
        except InvalidTokenError:
            raise credentials_exception
        user = self.user_repository.get_user_by_email(token_data.username)
        if user is None:
            raise credentials_exception
        return user
    
    
class KakaoUserService:
    def __init__(self, db: Session):
        self.user_repository = UserRepository(db)
    
    def authenticate_user(self, email: str, name: str):
        """Authenticate Kakao user and return tokens"""
        # Get or create Kakao user using repository
        user = self.user_repository.get_or_create_kakao_user(email, name)
        
        # Generate JWT tokens
        access_token = create_access_token(user.id, user.email)
        refresh_token = create_refresh_token(user.id, user.email)
        
        # Save refresh token linked by email
        self.user_repository.save_refresh_token(user.email, refresh_token)
        
        return {
            "user": user,
            "access_token": access_token,
            "refresh_token": refresh_token
        } 