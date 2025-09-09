from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.connection import get_db
from schema.travel_request import TravelLogCreateRequest
from schema.travel_response import TravelLogCreateResponse
from service.travel_service import TravelLogService
from utils.auth_util import JWTBearer
from fastapi import Body
from datetime import datetime
from schema.stamp_response import StampListResponse, StampResponse, CollectableStampResponse
from typing import Optional

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


@router.get(
    "/my_stamps",
    response_model=StampListResponse,
    responses={
        200: {"description": "Retrieved stamps list"},
        500: {"description": "Internal server error"}
    }
)
def get_users_stamps(
    session: Session = Depends(get_db),
    current_user: dict = Depends(JWTBearer())
):
    try:
        user_id = int(current_user["user_id"])
        travel_log_service = TravelLogService(session)
        stamps = travel_log_service.get_travel_stamps(user_id)
        stamp_responses = [
            StampResponse(
                id=stamp.id,
                title=stamp.title,  
                is_stamped=stamp.is_stamped,   
                stamped_at=stamp.stamped_at if stamp.stamped_at else None,
                latitude=stamp.location.latitude,
                longitude=stamp.location.longitude
            ) for stamp in stamps
        ]
        
        return StampListResponse(stamps=stamp_responses)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.patch(
    "/stamp/{stamp_id}/mark-completed",
    response_model=StampResponse,
    responses={
        200: {"description": "Stamp marked as completed"},
        500: {"description": "Internal server error"}
    }
)
def mark_stamp_completed(
    stamp_id: int,
    stamped_at: Optional[datetime] = Body(default=None, embed=True),
    current_user: dict = Depends(JWTBearer()),
    session: Session = Depends(get_db)
):
    try:
        user_id = int(current_user["user_id"])
    except (KeyError, ValueError, TypeError):
        raise HTTPException(status_code=403, detail="Invalid or expired token.")

    travel_log_service = TravelLogService(session)
    stamp = travel_log_service.update_stamp_completed(user_id, stamp_id, stamped_at)

    return StampResponse(
        id=stamp.id,
        title=stamp.title,
        is_stamped=stamp.is_stamped,
        stamped_at=stamp.stamped_at,
        latitude=stamp.location.latitude if stamp.location else None,
        longitude=stamp.location.longitude if stamp.location else None
    )


@router.get(
    "/stamp/collectable",
    response_model=CollectableStampResponse,
    responses={
        200: {"description": "Retrieved distance"},
        500: {"description": "Internal server error"}
    }
)
def get_collectable_stamps(
    latitude: float = Body(..., embed=True),
    longitude: float = Body(..., embed=True),
    current_user: dict = Depends(JWTBearer()),
    session: Session = Depends(get_db)
):
    try:
        user_id = int(current_user["user_id"])
        travel_log_service = TravelLogService(session)
        stamps = travel_log_service.get_collectable_stamps(user_id, latitude, longitude)
        return CollectableStampResponse(
            stamps=stamps)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")