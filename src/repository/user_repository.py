from sqlalchemy.orm import Session
from src.database.orm import User, KakaoUser
from typing import Optional, Tuple

class UserRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def find_by_email(self, email: str) -> Optional[User]:
        """Find user by email"""
        return self.db.query(User).filter(User.email == email).first()
    
    def find_by_kakao_id(self, kakao_id: int) -> Optional[User]:
        """Find user by Kakao ID"""
        return self.db.query(User).join(KakaoUser).filter(KakaoUser.id == kakao_id).first()
    
    def create_kakao_user(self, kakao_profile: dict) -> User:
        """Create new user from Kakao profile"""
        # Create main user
        user = User(
            username=kakao_profile["properties"]["nickname"], #???
            email=kakao_profile["kakao_account"]["email"],
            auth_provider="kakao",
        )
        self.db.add(user)
        self.db.flush()  # Get the user ID
        
        # Create Kakao user details
        kakao_user = KakaoUser(
            user_id=user.id,
            nickname=kakao_profile["properties"]["nickname"],
            profile_photo=kakao_profile["properties"].get("profile_image")
        )
        self.db.add(kakao_user)
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def get_or_create_kakao_user(self, kakao_profile: dict) -> Tuple[User, bool]:
        """
        Get existing user or create new one from Kakao profile
        Returns: (user, is_new_user)
        """
        # Check if user exists by email
        user = self.find_by_email(kakao_profile["kakao_account"]["email"])
        
        if user:
            # User exists, update if needed
            return user, False
        else:
            # Create new user
            user = self.create_kakao_user(kakao_profile)
            return user, True
    
    
