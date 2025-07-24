from sqlalchemy import Column, Integer, String, Text, Enum, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'user' #단수형으로 동일시키기.
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(255), unique=True, nullable=True) #for local only.
    email = Column(String(255), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=True)  #NB:  does not exist in kakao!
    name = Column(String(255), nullable=False)
    auth_provider = Column(Enum('local', 'kakao', name='auth_provider'), nullable=False, default='local')
    intro = Column(Text, nullable=True)
    language_cd = Column(Enum('KO', 'EN', 'JP', 'CN', 'FR', 'RU', name='language_cd'), nullable=True)
    gender = Column(Enum('female', 'male', 'unspecified', name='gender'), nullable=True)
    age = Column(Integer, nullable=True)
    thema = Column(Text, nullable=True)


    kakao = relationship("KakaoUser", back_populates="user", uselist=False, cascade='all, delete-orphan')


class KakaoUser(Base):
    __tablename__ = 'kakao_user'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, unique=True)

    nickname = Column(String(255), nullable=True)
    profile_photo = Column(String(255), nullable=True)

    user = relationship("User", back_populates="kakao")

class RefreshToken(Base):
    __tablename__ = 'refresh_token'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    token = Column(String(512), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="refresh_tokens")