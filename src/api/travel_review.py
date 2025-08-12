from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.connection import get_db
from schema.travel_review_request import TravelReviewCreateRequest
from schema.travel_review_response import TravelReviewCreateResponse
from service.travel_review_service import TravelReviewService
from utils.auth_util import JWTBearer

router = APIRouter(prefix="/travel")

@router.post(
    "/review",
    response_model=TravelReviewCreateResponse,
    responses={
        200: {"description": "Travel review created"},
        500: {"description": "Internal server error"}
    }
)
def create_travel_review_handler(
    request: TravelReviewCreateRequest,
    session: Session = Depends(get_db),
    payload: dict = Depends(JWTBearer()),
):
    try:
        try:
            user_id = int(payload["user_id"])
        except (KeyError, ValueError, TypeError):
            raise HTTPException(status_code=403, detail="Invalid or expired token.")

        service = TravelReviewService(session)
        saved_travel_review = service.create_travel_review(request, user_id=user_id)

        return TravelReviewCreateResponse.model_validate(saved_travel_review)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error")
