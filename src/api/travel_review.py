import logging
from typing import Annotated, List, Union

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from database.connection import get_db
from schema.travel_review_request import TravelReviewCreateRequest, Weather, ReviewTag
from schema.travel_review_response import TravelReviewCreateResponse
from service.travel_review_service import TravelReviewService
from utils.auth_util import JWTBearer

router = APIRouter(prefix="/travel")

# multipart/form-data용
TagInput = Annotated[Union[List[ReviewTag], List[str], str], Form(...)]

class TravelReviewForm:
    def __init__(
        self,
        travel_log_id: Annotated[int, Form(...)],
        title: Annotated[str, Form(...)],
        ai_rating: Annotated[float, Form(...)],
        started_at: Annotated[str, Form(...)],
        finished_at: Annotated[str, Form(...)],
        weather: Annotated[str, Form(...)],   # 이미 Enum이면 그대로 두세요
        mood: Annotated[float, Form(...)],
        tag: TagInput,                        # ← 핵심: 유니온으로 받기
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



@router.post(
    "/review",
    response_model=TravelReviewCreateResponse,
    responses={
        200: {"description": "Travel review created"},
        500: {"description": "Internal server error"}
    }
)
async def create_travel_review_handler(
    form: TravelReviewForm = Depends(),
    session: Session = Depends(get_db),
    payload: dict = Depends(JWTBearer()),
):
    try:
        try:
            user_id = int(payload["user_id"])
        except (KeyError, ValueError, TypeError):
            raise HTTPException(status_code=403, detail="Invalid or expired token.")

        # 필요 시 Enum 변환 (예: ReviewTag/Weather가 Enum이면)
        # weather_enum = Weather(form.weather)    # 값 검증 겸 변환
        # tags_enum = [ReviewTag(t) for t in form.tag]

        request = TravelReviewCreateRequest(
            travel_log_id=form.travel_log_id,
            title=form.title,
            ai_rating=form.ai_rating,
            started_at=form.started_at,
            finished_at=form.finished_at,
            weather=form.weather,  # 또는 weather_enum
            mood=form.mood,
            tag=form.tag,  # 또는 tags_enum
            note=form.note,
            song=form.song,
            picture=form.picture,
        )

        service = TravelReviewService(session)
        saved_travel_review = service.create_travel_review(request, user_id=user_id)

        return TravelReviewCreateResponse.model_validate(saved_travel_review)
    except Exception as e:
        logging.exception("create_travel_review_handler failed")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.delete(
    "/review/{review_id}",
    status_code=204,
    responses={
        200: {"description": "Travel review deleted"},
        500: {"description": "Internal server error"}
    }
)
def delete_travel_review_handler(
        review_id: int,
        session: Session = Depends(get_db),
        payload: dict = Depends(JWTBearer()),
):
    try:
        try:
            user_id = int(payload["user_id"])
        except (KeyError, ValueError, TypeError):
            raise HTTPException(status_code=403, detail="Invalid or expired token.")

        service = TravelReviewService(session)
        service.delete_travel_review(travel_review_id=review_id)

    except Exception as e:
        logging.exception("delete_travel_review_handler failed")
        raise HTTPException(status_code=500, detail="Internal Server Error")
