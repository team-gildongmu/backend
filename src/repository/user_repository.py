from sqlalchemy.orm import Session
from database.orm import KakaoUser
import logging

logger = logging.getLogger(__name__)

class KakaoUserRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def find_by_email(self, email: str) -> KakaoUser:
        """Find user by email"""
        return self.db.query(KakaoUser).filter(KakaoUser.email == email).first()
    
    def create_user(self, name: str, email: str, profile_photo: str = None) -> KakaoUser:
        """Create a new user"""
        try:
            logger.info(f"Creating user with name: {name}, email: {email}, profile_photo: {profile_photo}")
            
            # Ensure all values are strings or None
            name = str(name) if name is not None else None
            email = str(email) if email is not None else None
            profile_photo = str(profile_photo) if profile_photo is not None else None
            
            user = KakaoUser(
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
        except Exception as e:
            logger.error(f"Error creating user: {str(e)}")
            self.db.rollback()
            raise
    
    def get_or_create_user(self, email: str, name: str, profile_photo: str = None) -> KakaoUser:
        """Get existing user or create new one"""
        try:
            logger.info(f"Looking for user with email: {email}")
            user = self.find_by_email(email)
            print("==============================")
            print(user.email)
            
            if not user:
                logger.info("User not found, creating new user")
                user = self.create_user(name, email, profile_photo)
            # elif profile_photo and user.profile_photo != profile_photo:
            #     logger.info("Updating user's profile photo")
            #     user.profile_photo = profile_photo
            #     self.db.commit()
            #     self.db.refresh(user)
            
            return user
        except Exception as e:
            logger.error(f"Error in get_or_create_user: {str(e)}")
            raise 