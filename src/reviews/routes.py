from fastapi import APIRouter, status, Depends
from sqlmodel.ext.asyncio.session import AsyncSession
from .service import ReviewService
from .schema import ReviewCreateModel
from src.db.main import get_session
from src.db.models import User
from src.auth.dependencies import AccessTokenBearer, get_current_user

review_router = APIRouter()
review_service = ReviewService()
access_token_bearer =AccessTokenBearer()

@review_router.post("/book/{house_uid}")
async def add_reviews_to_house(
    review_data: ReviewCreateModel,
      house_uid: str, 
      session: AsyncSession=Depends(get_session),
      user: User= Depends(get_current_user),
      token_details: dict=Depends(access_token_bearer)):
    user_email = user.email

    review = await review_service.add_review(user_email, house_uid, review_data, session)

    return review

@review_router.get("/{review_uid}")
async def get_review_by_uid(
    review_uid: str,
      session: AsyncSession=Depends(get_session),
      token_details: dict=Depends(access_token_bearer)):
    
    review = await review_service.get_review(review_uid, session)
    return review

@review_router.get("/house/{house_uid}")
async def get_house_reviews(
    house_uid: str,
      session: AsyncSession=Depends(get_session),
      token_details: dict=Depends(access_token_bearer)):
    
    review = await review_service.get_all_house_review(house_uid=house_uid, session=session)
    return review

@review_router.delete("/{review_id}")
async def delete_review_by_uid(
    review_uid: str,
      session: AsyncSession=Depends(get_session),
      token_details: dict=Depends(access_token_bearer),
      user: User= Depends(get_current_user)):
    current_user_uid = user.uid

    review = await review_service.delete_review(current_user_uid, review_uid,session)
    return review