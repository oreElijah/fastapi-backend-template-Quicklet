from sqlmodel import select, desc
from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi.exceptions import HTTPException
from fastapi import status
import logging
import uuid
from src.db.models import Review
from src.auth.service import UserService
from src.houses.service import HouseService
from .schema import ReviewCreateModel

user_service = UserService()
house_service = HouseService()

class ReviewService:
    async def add_review(self, user_email: str,house_uid: str, review_data: ReviewCreateModel, session: AsyncSession):
        try:
            house = await house_service.get_house_by_id(house_uid, session)
            user = await user_service.get_user_by_email(email=user_email, session=session)

            review_data_dict = review_data.model_dump()
            new_review = Review(
                **review_data_dict
            )
            if not house:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Book not found"
                )
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            new_review.user = user

            new_review.houses = house

            session.add(new_review)

            await session.commit()

            rating = await self.get_book_cummulative_rating(new_review.house_uid, session)
            await house_service.update_house_by_id({"rating": rating}, new_review.house_uid, session)

            return new_review
        except Exception as e:
            logging.exception(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Oops ... Something went wrong"
            )
    
    async def get_review(self, review_uid:str, session: AsyncSession):
        try:
            stmt = select(Review).where(review_uid==Review.uid)

            result = await session.exec(stmt)

            return result.first()
    
        except Exception as e:
            logging.exception(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Oops ... Something went wrong"
            )
    
    async def get_all_house_review(self, house_uid: str, session: AsyncSession):
        try:
            stmt = select(Review).where(Review.house_uid==house_uid).order_by(desc(Review.created_at))

            result = await session.exec(stmt)

            reviews = result.all()

            return [
                {
                    "review_uid": str(review.uid),
                    "review_text": review.review_text,
                    "review_rate": review.rating
                }
                for review in reviews
            ]

        except Exception as e:
            logging.exception(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Oops ... Something went wrong"
            )
    
    async def delete_review(self,current_user_uid: str, review_uid: str, session: AsyncSession):
        try:
            review = await self.get_review(review_uid, session)

            if current_user_uid==review.user_uid:

                session.delete(review)
                session.refresh(review)

                await session.commit()
                return {
                    "message": "Review deleted"
                }
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can't delete others review"
            )
        except Exception as e:
            logging.exception(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Oops ... Something went wrong"
            )
        
    async def get_book_cummulative_rating(self, house_uid: str, session: AsyncSession):
        cummulative_rating = 0
        try:
            stmt = select(Review).where(Review.house_uid==house_uid)

            result = await session.exec(stmt)
            reviews = result.all()

            if len(reviews)==0:
                return cummulative_rating
            for review in reviews:
                cummulative_rating += review.rating
            cummulative_rating = cummulative_rating/len(reviews)
            return cummulative_rating
        except Exception as e:
            logging.exception(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Oops ... Something went wrong"
            )
