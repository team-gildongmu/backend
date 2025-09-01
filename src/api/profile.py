from fastapi import APIRouter, Depends, HTTPException, Form, File, UploadFile
from sqlalchemy.orm import Session
from database.connection import get_db
from service.user_service import UserService
from utils.auth_util import JWTBearer
from typing import Optional
import logging
from schema.profile_response import ProfileResponse
# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/profile")

@router.patch("/edit", responses={
    200: {"description": "Profile updated successfully"},
    400: {"description": "Invalid request"},
    500: {"description": "Internal server error"}
})
async def edit_profile(
    nickname: Optional[str] = Form(None),
    intro: Optional[str] = Form(None),
    profile_photo: Optional[UploadFile] = File(None),
    current_user = Depends(JWTBearer()),
    db: Session = Depends(get_db)
):
    """
    Edit user profile with optional nickname, intro, and profile photo.
    At least one field must be provided.
    """
    try:

        user_id = int(current_user["user_id"])
        

        if nickname is None and intro is None and profile_photo is None:
            raise HTTPException(
                status_code=400, 
                detail="At least one field (nickname, intro, profile_photo) must be provided"
            )
        

        user_service = UserService(db)
        updated = user_service.update_profile(
            user_id=user_id,
            nickname=nickname,
            intro=intro,
            image=profile_photo
        )
        
        return {
            "success": True,
            "message": "Profile updated successfully",
            "updated_fields": updated
        }
        
    except ValueError as ve:
        logger.error(f"Validation error: {str(ve)}")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Error updating profile: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    

@router.get("/me", response_model=ProfileResponse, responses={
    200: {"description": "Profile retrieved successfully"},
    400: {"description": "Invalid request"},
    500: {"description": "Internal server error"}
})
async def get_profile(
    current_user = Depends(JWTBearer()),
    db: Session = Depends(get_db),
    
):
    try:
        user_id = int(current_user["user_id"])
        user_service = UserService(db)
        return user_service.get_profile(user_id)
        
    except Exception as e:
        logger.error(f"Error getting profile: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")