from enum import Enum
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel


class Weather(str, Enum):
    sunny  = "sunny"
    cloudy = "cloudy"
    rainy  = "rainy"
    snowy  = "snowy"

WEATHER_LABELS = {
    "sunny": "맑음",
    "cloudy": "흐림",
    "rainy": "비",
    "snowy": "눈",
}

class ReviewTag(str, Enum):
    clean_and_comfy      = "clean_and_comfy"
    tasty_food           = "tasty_food"
    healing              = "healing"
    beautiful_view       = "beautiful_view"
    want_to_come_again   = "want_to_come_again"
    kind_staff           = "kind_staff"
    quiet_and_relaxing   = "quiet_and_relaxing"
    nice_atmosphere      = "nice_atmosphere"
    special_memory       = "special_memory"
    good_for_photos      = "good_for_photos"

REVIEW_TAG_LABELS = {
    "clean_and_comfy": "깨끗하고 편안해요",
    "tasty_food": "음식이 맛있어요",
    "healing": "힐링하기 좋아요",
    "beautiful_view": "경치가 아름다워요",
    "want_to_come_again": "다시 오고 싶어요",
    "kind_staff": "직원들이 친절해요",
    "quiet_and_relaxing": "조용하고 여유로워요",
    "nice_atmosphere": "분위기가 좋아요",
    "special_memory": "특별한 추억이 생겨요",
    "good_for_photos": "사진 찍기 좋아요",
}

class TravelReviewCreateRequest(BaseModel):
    travel_log_id: int
    title: str
    ai_rating: float
    started_at: str
    finished_at: str
    weather: Weather
    mood: float
    picture: List[UploadFile] #url
    tag: List[ReviewTag]
    note: str
    song: str
