from enum import Enum
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from typing import Annotated, List, Union

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

# multipart/form-data용
TagInput = Annotated[Union[List[ReviewTag], List[str], str], Form(...)]
WeatherInput = Annotated[Weather, Form(...)]

class TravelReviewForm:
    def __init__(
        self,
        travel_log_id: Annotated[int, Form(...)],
        title: Annotated[str, Form(...)],
        ai_rating: Annotated[float, Form(...)],
        started_at: Annotated[str, Form(...)],
        finished_at: Annotated[str, Form(...)],
        weather: WeatherInput,
        mood: Annotated[float, Form(...)],
        tag: TagInput,
        note: Annotated[str, Form(...)],
        song: Annotated[str, Form(...)],
        picture: Annotated[List[UploadFile], File(...)]
    ):
        # --- tag 정규화 시작 ---
        # tag가 str이면 "a,b,c" → ["a","b","c"]
        # tag가 list[str]이면 각 요소를 다시 콤마 분해해 합치기
        # tag가 list[ReviewTag]이면 그대로 값만 추출
        raw_items: List[str] = []

        if isinstance(tag, str):
            raw_items = [p.strip() for p in tag.split(",") if p.strip()]
        elif isinstance(tag, list):
            for item in tag:
                if isinstance(item, ReviewTag):
                    raw_items.append(item.value)
                elif isinstance(item, str):
                    # ["a,b,c"] 같은 케이스 방지용
                    raw_items.extend([p.strip() for p in item.split(",") if p.strip()])
                else:
                    raise ValueError("Invalid tag item")

        # Enum 캐스팅 (유효하지 않은 값이면 422로 오류 발생)
        self.tag: List[ReviewTag] = [ReviewTag(v) for v in raw_items]
        # --- tag 정규화 끝 ---

        self.travel_log_id = travel_log_id
        self.title = title
        self.ai_rating = ai_rating
        self.started_at = started_at
        self.finished_at = finished_at
        self.weather = weather
        self.mood = mood
        self.note = note
        self.song = song
        self.picture = picture

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


class TravelReviewUpdateForm:
    def __init__(
        self,
        review_id: Annotated[int, Form(...)],
        title: Annotated[Optional[str], Form(...)],
        ai_rating: Annotated[Optional[float], Form(...)],
        started_at: Annotated[Optional[str], Form(...)],
        finished_at: Annotated[Optional[str], Form(...)],
        weather: WeatherInput,
        mood: Annotated[Optional[float], Form(...)],
        tag: TagInput,  # ← 핵심: 유니온으로 받기
        note: Annotated[str, Form(...)],
        song: Annotated[str, Form(...)],
        picture: Annotated[List[UploadFile], File(...)]
    ):
        # --- tag 정규화 시작 ---
        # tag가 str이면 "a,b,c" → ["a","b","c"]
        # tag가 list[str]이면 각 요소를 다시 콤마 분해해 합치기
        # tag가 list[ReviewTag]이면 그대로 값만 추출
        raw_items: List[str] = []

        if isinstance(tag, str):
            raw_items = [p.strip() for p in tag.split(",") if p.strip()]
        elif isinstance(tag, list):
            for item in tag:
                if isinstance(item, ReviewTag):
                    raw_items.append(item.value)
                elif isinstance(item, str):
                    # ["a,b,c"] 같은 케이스 방지용
                    raw_items.extend([p.strip() for p in item.split(",") if p.strip()])
                else:
                    raise ValueError("Invalid tag item")

        # Enum 캐스팅 (유효하지 않은 값이면 422로 오류 발생)
        self.tag: List[ReviewTag] = [ReviewTag(v) for v in raw_items]
        # --- tag 정규화 끝 ---

        self.review_id = review_id
        self.title = title
        self.ai_rating = ai_rating
        self.started_at = started_at
        self.finished_at = finished_at
        self.weather = weather
        self.mood = mood
        self.note = note
        self.song = song
        self.picture = picture


class TravelReviewUpdateRequest(BaseModel):
    review_id: int
    title: Optional[str] = None
    ai_rating: Optional[float] = None
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    weather: Optional[Weather] = None
    mood: Optional[float] = None
    tag: Optional[List["ReviewTag"]] = None
    note: Optional[str] = None
    song: Optional[str] = None
    picture: Optional[List[UploadFile]] = None

    class Config:
        arbitrary_types_allowed = True