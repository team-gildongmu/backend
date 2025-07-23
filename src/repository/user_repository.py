from sqlalchemy.orm import Session
from database.orm import User

class KakaoUserRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def find_by_email(self, email: str) -> User:
        """Find user by email"""
        return self.db.query(User).filter(User.email == email).first()
    
    def create_user(self, name: str, email: str, profile_photo: str = None) -> User:
        """Create a new user"""
        user = User(
            name=name, 
            email=email, 
            nickname=name,  # Use name as initial nickname
            profile_photo=profile_photo,
            intro=None, 
            language_cd=None
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def get_or_create_user(self, email: str, name: str, profile_photo: str = None) -> User:
        """Get existing user or create new one"""
        user = self.find_by_email(email)
        if not user:
            user = self.create_user(name, email, profile_photo)
        elif profile_photo and user.profile_photo != profile_photo:
            # Update profile photo if changed
            user.profile_photo = profile_photo
            self.db.commit()
            self.db.refresh(user)
        return user 