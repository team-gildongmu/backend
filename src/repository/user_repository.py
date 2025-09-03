from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload
from database.orm import User, KakaoUser
from typing import Optional, Tuple, Dict
from models.profile import ProfileData

class UserRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def find_by_email(self, email: str) -> Optional[User]:
        """Find user by email"""
        return self.db.query(User).filter(User.email == email).first()
    
    def find_by_kakao_id(self, kakao_id: int) -> Optional[User]:
        """Find user by Kakao ID"""
        return self.db.query(User).join(KakaoUser).filter(KakaoUser.id == kakao_id).first()

    
    def find_kakao_by_user_id(self, user_id: int) -> Optional[KakaoUser]:
        """Return KakaoUser row for a given User.id"""
        return self.db.query(KakaoUser).filter(KakaoUser.user_id == user_id).first()
    
    def create_kakao_user(self, kakao_profile: dict) -> User:
        """Create new user from Kakao profile"""
        """
        Input: 
        {
            "id": "REDACTED_USER_ID",
            "connected_at": "2025-07-23T00:33:59Z",
            "properties": {
                "nickname": "REDACTED_NICKNAME",
                "profile_image": "REDACTED_IMAGE_URL",
                "thumbnail_image": "REDACTED_IMAGE_URL"
            },
            "kakao_account": {
                "profile_nickname_needs_agreement": false,
                "profile_image_needs_agreement": false,
                "profile": {
                "nickname": "REDACTED_NICKNAME",
                "thumbnail_image_url": "REDACTED_IMAGE_URL",
                "profile_image_url": "REDACTED_IMAGE_URL",
                "is_default_image": false,
                "is_default_nickname": false
                },
                "has_email": true,
                "email_needs_agreement": false,
                "is_email_valid": true,
                "is_email_verified": true,
                "email": "REDACTED_EMAIL"
            }
            }
        """
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
            ### Profile image OT thumbnail..?
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
    
    
    def update_profile(self, user_id: int, *, nickname: Optional[str] = None, intro: Optional[str] = None, profile_photo_key: Optional[str] = None) -> Dict:
        """
        Update user's profile fields.

        - Updates `User.intro` when provided
        - Updates `KakaoUser.nickname` and/or `KakaoUser.profile_photo` when provided
        - At least one of the fields must be provided by the caller
        """
        updated: Dict = {}


        if intro is not None:
            user: Optional[User] = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError("User not found")
            user.intro = intro
            updated["intro"] = intro

        if nickname is not None or profile_photo_key is not None:
            kakao_user: Optional[KakaoUser] = self.db.query(KakaoUser).filter(KakaoUser.user_id == user_id).first()
            if not kakao_user:

                raise ValueError("Kakao user profile not found for this user")

            if nickname is not None:
                kakao_user.nickname = nickname
                updated["nickname"] = nickname

            if profile_photo_key is not None:
                kakao_user.profile_photo = profile_photo_key
                updated["profile_photo_key"] = profile_photo_key


        if updated:
            self.db.commit()
        
        return updated
    
    def get_profile(self, user_id: int) -> ProfileData:
        user = self.db.query(User).options(joinedload(User.kakao)).filter(User.id == user_id).first()
        if not user or not user.kakao:
            raise ValueError(f"User profile not found for user id {user_id}")

        return ProfileData(
            nickname=user.kakao.nickname,
            email=user.email,
            intro=user.intro,
            profile_photo_key=user.kakao.profile_photo)
    

