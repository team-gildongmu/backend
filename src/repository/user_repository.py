from sqlalchemy.orm import Session
from database.orm import User, KakaoUser, RefreshToken

class UserRepository:
    def __init__(self, db: Session):
        self.db = db
    
    # User methods (for email/password authentication)
    def get_user_by_email(self, email: str) -> User:
        """Get user by email for traditional login"""
        return self.db.query(User).filter(User.email == email).first()
    
    def get_user_by_username(self, username: str) -> User:
        """Get user by username"""
        return self.db.query(User).filter(User.username == username).first()
    
    def create_user(self, username: str, email: str, hashed_password: str) -> User:
        """Create a new traditional user with hashed password"""
        user = User(
            username=username,
            email=email,
            hashed_password=hashed_password,
            name=username  # Using username as name for simplicity
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def save_refresh_token(self, email: str, token: str) -> RefreshToken:
        """Save refresh token linked by email"""
        refresh_token = RefreshToken(
            email=email,
            token=token
        )
        self.db.add(refresh_token)
        self.db.commit()
        self.db.refresh(refresh_token)
        return refresh_token
    
    def get_refresh_token(self, token: str) -> RefreshToken:
        """Get refresh token by token string"""
        return self.db.query(RefreshToken).filter(RefreshToken.token == token).first()
    
    def delete_refresh_token(self, token: str):
        """Delete refresh token (for logout)"""
        refresh_token = self.get_refresh_token(token)
        if refresh_token:
            self.db.delete(refresh_token)
            self.db.commit()
    
    # KakaoUser methods (for social login)
    def find_kakao_user_by_email(self, email: str) -> KakaoUser:
        """Find Kakao user by email"""
        return self.db.query(KakaoUser).filter(KakaoUser.email == email).first()
    
    def create_kakao_user(self, name: str, email: str) -> KakaoUser:
        """Create a new Kakao user"""
        user = KakaoUser(
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
    
    def get_or_create_kakao_user(self, email: str, name: str) -> KakaoUser:
        """Get existing Kakao user or create new one"""
        user = self.find_kakao_user_by_email(email)
        if not user:
            user = self.create_kakao_user(name, email)
        return user
#