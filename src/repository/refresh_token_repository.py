from typing import Optional
from sqlalchemy.orm import Session
from database.orm import RefreshToken


class RefreshTokenRepository:
    def __init__(self, db: Session):
        self.db = db

    def save(self, user_id: int, token: str) -> RefreshToken:
        refresh_token = RefreshToken(user_id=user_id, token=token)
        self.db.add(refresh_token)
        self.db.commit()
        self.db.refresh(refresh_token)
        return refresh_token

    def find_by_token(self, token: str) -> Optional[RefreshToken]:
        return (
            self.db.query(RefreshToken)
            .filter(RefreshToken.token == token)
            .first()
        )

    def delete_by_token(self, token: str) -> None:
        self.db.query(RefreshToken).filter(RefreshToken.token == token).delete()
        self.db.commit()

    def delete_all_for_user(self, user_id: int) -> None:
        self.db.query(RefreshToken).filter(RefreshToken.user_id == user_id).delete()
        self.db.commit()


