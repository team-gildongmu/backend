from sqlalchemy import Column, Integer, String, Text, Enum, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

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