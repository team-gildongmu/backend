# src/schema/ai_trip.py
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class Coords(BaseModel):
    mapX: float
    mapY: float

class StartSessionRequest(BaseModel):
    origin: Optional[Coords] = None
    days: int = 1
    mode: str = "walk"
    tags: List[str] = Field(default_factory=list)

class StartSessionResponse(BaseModel):
    session_id: str

class MessageRequest(BaseModel):
    message: str
    origin: Optional[Coords] = None
    days: Optional[int] = None
    mode: Optional[str] = None
    tags: Optional[List[str]] = None

class MessageResponse(BaseModel):
    plan: Dict[str, Any]
    status: Dict[str, str]

class StateResponse(BaseModel):
    state: Dict[str, Any]
