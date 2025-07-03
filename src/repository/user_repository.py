from sqlalchemy.orm import Session
from src.database.orm import User

class UserRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def find_by_email(self, email: str) -> User:
        """Find user by email"""
        return self.db.query(User).filter(User.email == email).first()
    
    def create_user(self, name: str, email: str) -> User:
        """Create a new user"""
        user = User(
            name=name, 
            email=email, 
            nickname=None, 
            profile_photo=None, 
            intro=None, 
            language_cd=None
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def get_or_create_user(self, email: str, name: str) -> User:
        """Get existing user or create new one"""
        user = self.find_by_email(email)
        if not user:
            user = self.create_user(name, email)
        return user 