from sqlalchemy.orm import Session
from database.orm import User, KakaoUser
import logging

logger = logging.getLogger(__name__)

class KakaoUserRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def find_by_email(self, email: str) -> KakaoUser:
        """Find user by email"""
        return self.db.query(KakaoUser).filter(KakaoUser.email == email).first()
    
    def create_user(self, name: str, email: str, auth_provider: str = 'kakao', hashed_password: str = None) -> User:
        """Create a new user"""
        user = User(
            name=name, 
            email=email,
            auth_provider=auth_provider,
            hashed_password=hashed_password,  # Will be None for Kakao users
            intro=None,  #write later
            language_cd=None #write later
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def create_kakao_user(self, user_id: int, nickname: str, profile_photo: str = None) -> KakaoUser:
        """Create a new Kakao user profile"""
        kakao_user = KakaoUser(
            user_id=user_id,
            nickname=nickname,
            profile_photo=profile_photo
        )
        self.db.add(kakao_user)
        self.db.commit()
        self.db.refresh(kakao_user)
        return kakao_user
    
    def get_or_create_kakao_user(self, email: str, name: str, nickname: str = None, profile_photo: str = None) -> User:
        """Get existing user or create new Kakao user with profile"""
        user = self.find_by_email(email)
        
        if not user:
            # Create main user (always kakao for this method)
            user = self.create_user(name, email, auth_provider='kakao')
            
            self.create_kakao_user(user.id, nickname, profile_photo)
        
        return user
    
