from sqlalchemy import Column, Integer, String, Text, Enum, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

from sqlalchemy.sql.sqltypes import Float

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
    user = relationship('User', back_populates='refresh_tokens')


class TravelLog(Base):
    __tablename__ = "travel_log"
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    title = Column(String(256), nullable=False)
    user_id = Column(Integer, ForeignKey("user.id")) # 외래키

class TravelLocation(Base) :
    __tablename__ = "travel_location"
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    travel_log_id = Column(Integer, ForeignKey("travel_log.id"))  # 외래키
    user_id = Column(Integer, ForeignKey("user.id")) # 외래키
    name = Column(String(256), nullable=False)
    sequence = Column(Integer, nullable=False)
    longitude = Column(Float, nullable=False)
    latitude = Column(Float, nullable=False)
    congestion = Column(String(256), nullable=False)

class TravelStamp(Base) :
    __tablename__ = "travel_stamp"
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    travel_log_id = Column(Integer, ForeignKey("travel_log.id"))  # 외래키
    travel_location_id = Column(Integer, ForeignKey("travel_location.id"))  # 외래키
    user_id = Column(Integer, ForeignKey("user.id")) # 외래키
    title = Column(String(256), nullable=False)
    emotion = Column(String(256), nullable=False)
    isStamped = Column(Boolean, nullable=False)
    stamped_at = Column(DateTime, nullable=False)
