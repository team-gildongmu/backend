import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.connection import get_db
from schema.travel_log_request import TravelLogCreateRequest
from schema.travel_log_response import TravelLogCreateResponse, TravelLogResponse, TravelLogMapResponse
from service.travel_log_service import TravelLogService
from utils.auth_util import JWTBearer

router = APIRouter(prefix="/travel")

@router.post(
    "/log",
    response_model=TravelLogCreateResponse,
    responses={
        200: {"description": "Travel log created"},
        500: {"description": "Internal server error"}
    }
)
def create_travel_log_handler(
    request: TravelLogCreateRequest,
    session: Session = Depends(get_db),
    payload: dict = Depends(JWTBearer()),
):
    try:
        try:
            user_id = int(payload["user_id"])
        except (KeyError, ValueError, TypeError):
            raise HTTPException(status_code=403, detail="Invalid or expired token.")


        service = TravelLogService(session)
        saved_travel_log = service.create_travel_log(request, user_id=user_id)

        return TravelLogCreateResponse.model_validate(saved_travel_log)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.get("/log/list")
def get_travel_log_list_handler(
        theme: str | None = None,
        session: Session = Depends(get_db),
        payload: dict = Depends(JWTBearer()),
):
    try:
        try:
            user_id = int(payload["user_id"])
        except (KeyError, ValueError, TypeError):
            raise HTTPException(status_code=403, detail="Invalid or expired token.")

        service = TravelLogService(session)
        return service.get_travel_log_list_handler(user_id=user_id, theme=theme)

    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.get(
    "/log",
    response_model=TravelLogResponse,
)
def get_travel_log_handler(
        travel_log_id: int,
        session: Session = Depends(get_db),
        payload: dict = Depends(JWTBearer()),
):
    try:
        try:
            user_id = int(payload["user_id"])
        except (KeyError, ValueError, TypeError):
            raise HTTPException(status_code=403, detail="Invalid or expired token.")

        service = TravelLogService(session)
        return service.get_travel_log_handler(travel_log_id=travel_log_id, user_id=user_id)

    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.get(
    "/log/map",
    response_model = TravelLogMapResponse,
)
def get_travel_log_handler(
        travel_log_id: int,
        session: Session = Depends(get_db),
        payload: dict = Depends(JWTBearer()),
):
    try:
        try:
            user_id = int(payload["user_id"])
        except (KeyError, ValueError, TypeError):
            raise HTTPException(status_code=403, detail="Invalid or expired token.")

        service = TravelLogService(session)
        return service.get_travel_log_map_handler(travel_log_id=travel_log_id, user_id=user_id)

    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error")