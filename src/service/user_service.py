from sqlalchemy.orm import Session
from src.repository.user_repository import UserRepository
from src.utils.jwt_utils import create_access_token, create_refresh_token

class UserService:
    def __init__(self, db: Session):
        self.user_repository = UserRepository(db)
    
    def authenticate_user(self, email: str, name: str):
        """Authenticate user and return tokens"""
        # Get or create user using repository
        user = self.user_repository.get_or_create_user(email, name)
        
        # Generate JWT tokens
        access_token = create_access_token(user.id, user.email)
        refresh_token = create_refresh_token(user.id, user.email)
        
        return {
            "user": user,
            "access_token": access_token,
            "refresh_token": refresh_token
        } 