from sqlalchemy.orm import Session
from repository.user_repository import UserRepository
from service.token_service import TokenService, SECRET_KEY, ALGORITHM
from utils.hash_password import verify_password, hash_password
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from jwt.exceptions import InvalidTokenError
from passlib.context import CryptContext
from schema.response import TokenData

class UserService:
    def __init__(self, db: Session):
        self.user_repository = UserRepository(db)
        self.token_service = TokenService()
    
    def authenticate_user(self, email: str, password: str):
        """Authenticate user with email and password"""
        user = self.user_repository.get_user_by_email(email)
        if not user:
            return False
        if not verify_password(password, user.hashed_password):
            return False
        return user
    
    def create_user(self, username: str, email: str, password: str):
        """Create a new user with hashed password"""
        # Check if user already exists
        existing_user = self.user_repository.get_user_by_username(username)
        if existing_user:
            raise HTTPException(status_code=400, detail="Username already registered")
        
        existing_email = self.user_repository.get_user_by_email(email)
        if existing_email:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Hash password and create user
        hashed_password = hash_password(password)
        return self.user_repository.create_user(username, email, hashed_password)
    
    def create_tokens_for_user(self, user):
        """Create access and refresh tokens for user and save refresh token"""
        
        # Use TokenService to create tokens
        access_token = self.token_service.create_access_token(data={"sub": user.email})
        refresh_token = self.token_service.create_refresh_token(data={"sub": user.email})
        
        # Save refresh token linked by email
        self.user_repository.save_refresh_token(user.email, refresh_token)
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token
        }
    
    async def get_current_user(self, token: Annotated[str, Depends()]):
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
        self.token_service = TokenService()
    
    def authenticate_user(self, email: str, name: str):
        """Authenticate Kakao user and return tokens"""
        # Get or create Kakao user using repository
        user = self.user_repository.get_or_create_kakao_user(email, name)
        
        # Use TokenService to create tokens
        access_token = self.token_service.create_access_token(data={"sub": user.email})
        refresh_token = self.token_service.create_refresh_token(data={"sub": user.email})
        
        # Save refresh token linked by email
        self.user_repository.save_refresh_token(user.email, refresh_token)
        
        return {
            "user": user,
            "access_token": access_token,
            "refresh_token": refresh_token
        } 
    #