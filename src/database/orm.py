from sqlalchemy import Column, Integer, String, Text, Enum, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

from sqlalchemy.sql.sqltypes import Float

Base = declarative_base()

class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, unique=True)
    nickname = Column(String(255), nullable=True)
    profile_photo = Column(String(255), nullable=True)
    intro = Column(Text, nullable=True)
    language_cd = Column(Enum('KO', 'EN', 'JP', 'CN', 'FR', 'RU', name='language_cd'), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    refresh_tokens = relationship('RefreshToken', back_populates='user')

class RefreshToken(Base):
    __tablename__ = 'refresh_token'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    token = Column(String(512), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    user = relationship('User', back_populates='refresh_tokens')

class TravelLog(Base) :
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
