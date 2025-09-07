from typing import List
from pydantic import BaseModel

class Location(BaseModel):
    mapx: float # longitude
    mapy: float # latitude


class TravelLocationCreateRequest(BaseModel):
    type: str   # POI, MEAL 등
    title: str
    desc: str
    reason: str
    image: str
    coords: Location
    # sequence: int
    # congestion: str

class DayPlanCreateRequest(BaseModel):
    segments: List[TravelLocationCreateRequest]

class StayCreateRequest(BaseModel):
    title: str
    desc: str
    image: str
    coords: Location

class TravelLogCreateRequest(BaseModel):
    title: str
    keywords: List[str]  # 키워드
    days: List[DayPlanCreateRequest]  # 일자별 여행지 리스트
    stays: List[StayCreateRequest]  # 숙소 리스트
    summary: str  # 전체 여행 요약