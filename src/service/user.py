from src.database.orm import User
from sqlalchemy.orm import Session

def get_or_create_user(db: Session, email: str, name: str):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(name=name, email=email, nickname=None, profile_photo=None, intro=None, language_cd=None)
        db.add(user)
        db.commit()
        db.refresh(user)
    return user 