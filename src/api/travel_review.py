import logging
from typing import Annotated, List, Union

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from database.connection import get_db
from schema.travel_review_request import TravelReviewCreateRequest, Weather, ReviewTag, TravelReviewUpdateForm, \
    TravelReviewUpdateRequest, TravelReviewForm
from schema.travel_review_response import TravelReviewCreateResponse
from service.travel_review_service import TravelReviewService
from utils.auth_util import JWTBearer

from schema.travel_review_response import TravelReviewListResponse

router = APIRouter(prefix="/travel")

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


@router.put("/review")
async def update_travel_review_handler(
    form: TravelReviewUpdateForm = Depends(),
    session: Session = Depends(get_db),
    payload: dict = Depends(JWTBearer()),
):
    try:
        try:
            user_id = int(payload.get("user_id"))
        except (KeyError, ValueError, TypeError):
            raise HTTPException(status_code=403, detail="Invalid or expired token.")

        request = TravelReviewUpdateRequest(
            review_id=form.review_id,
            title=form.title,
            ai_rating=form.ai_rating,
            started_at=form.started_at,
            finished_at=form.finished_at,
            weather=form.weather,
            mood=form.mood,
            tag=form.tag,
            note=form.note,
            song=form.song,
            picture=form.picture,
        )

        service = TravelReviewService(session)
        updated_review = service.update_travel_review(request, user_id=user_id)

    except Exception as e:
        logging.exception("update_travel_review_handler failed")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.get("/review", status_code=200)
def get_travel_review(
        travel_review_id: int,
        session: Session = Depends(get_db),
        payload: dict = Depends(JWTBearer()),
):
    try:
        try:
            user_id = int(payload["user_id"])
        except (KeyError, ValueError, TypeError):
            raise HTTPException(status_code=403, detail="Invalid or expired token.")

        service = TravelReviewService(session)
        return service.get_travel_review(travel_review_id=travel_review_id)

    except Exception as e:
        logging.exception("get_travel_review failed")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.get(
    "/review/list",
    response_model=List[TravelReviewListResponse],
    status_code=200
)
def get_travel_review_list_handler(
        session: Session = Depends(get_db),
        payload: dict = Depends(JWTBearer()),
):
    try:
        try:
            user_id = int(payload["user_id"])
        except (KeyError, ValueError, TypeError):
            raise HTTPException(status_code=403, detail="Invalid or expired token.")

        service = TravelReviewService(session)
        return service.get_travel_review_list(user_id=user_id)

    except Exception as e:
        logging.exception("get_travel_review_list_handler failed")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.get("/review/calendar", status_code=200)
def get_travel_review_calendar_handler(
        session: Session = Depends(get_db),
        payload: dict = Depends(JWTBearer()),
):
    try:
        try:
            user_id = int(payload["user_id"])
        except (KeyError, ValueError, TypeError):
            raise HTTPException(status_code=403, detail="Invalid or expired token.")

        service = TravelReviewService(session)
        return service.get_travel_review_calendar(user_id=user_id)

    except Exception as e:
        logging.exception("get_travel_review_calendar_handler failed")
        raise HTTPException(status_code=500, detail="Internal Server Error")