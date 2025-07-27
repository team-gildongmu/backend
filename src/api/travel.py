from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.connection import get_db
from schema.travel_request import TravelLogCreateRequest
from schema.travel_response import TravelLogCreateResponse
from service.travel_service import TravelLogService

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
):
    try:
        service = TravelLogService(session)
        saved_travel_log = service.create_travel_log(request)
        return TravelLogCreateResponse.model_validate(saved_travel_log)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error")
