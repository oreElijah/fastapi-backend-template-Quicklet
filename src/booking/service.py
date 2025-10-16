from fastapi import status, HTTPException
from fastapi.responses import JSONResponse
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from datetime import datetime, timezone, timedelta
import uuid
from src.booking.model import Booking
from src.booking.schema import BookingCreateModel
from src.db.models import House
from src.houses.service import HouseService
from src.auth.service import UserService
from src.auth.utils import nights_in_between
from src.mail.mail import mails, create_message
from sqlalchemy import func

RESERVATION_EXPIRY_MINUTE = 15
house_service = HouseService()
user_service = UserService()

class BookingService:
    async def is_house_available(self, house_uid: str, start_date: datetime, end_date: datetime, session: AsyncSession):
        stmt = select(Booking).where(
            (Booking.house_uid == house_uid) &
            (
                (Booking.start_date <= end_date) &
                (Booking.end_date >= start_date)&
                (House.Available==True)
            )
        )
        result = await session.exec(stmt)
        return not result.first()
    
    async def book_house(self, booking_data: BookingCreateModel, session: AsyncSession):
        available = await self.is_house_available(
            booking_data.house_uid,
            booking_data.start_date,
            booking_data.end_date,
            session
        )
        if not available:
            return None
        house = await house_service.get_house_by_id(booking_data.house_uid, session)
        nights = nights_in_between(booking_data.start_date, booking_data.end_date)
        amount = int(nights * house.price_per_night)

        expires_at = datetime.now() + timedelta(minutes=RESERVATION_EXPIRY_MINUTE)

        new_booking = Booking(**booking_data.model_dump())
        new_booking.status = "pending"
        new_booking.amount =amount
        new_booking.expires_at = expires_at
        session.add(new_booking)
        house.Available=False
        await session.commit()
        await session.refresh(new_booking)
        return new_booking
    
    async def get_specific_booking(self, booking_uid: str, session: AsyncSession):
        stmt = select(Booking).where(booking_uid==Booking.booking_uid)

        result = await session.exec(stmt)

        return result.first()
    
    async def get_details_specific_booking(self, booking_uid: str, session: AsyncSession):
        booking = await self.get_specific_booking(booking_uid, session)
        if not booking:
            return None
        house_uid = booking.house_uid

        details = await house_service.get_house_by_id(house_uid, session)

        return details
    
    async def get_users_booking_history(self, user_uid: str, session: AsyncSession): #for users to check their booking history
        stmt = select(Booking).where(user_uid==Booking.user_uid)

        result = await session.exec(stmt)

        return result.all()
    
    async def get_all_bookings(self, session: AsyncSession):
        stmt = select(Booking)

        result = await session.exec(stmt)

        return result.all()

    async def get_all_booking_for_house(self, house_uid: str, user_id: str, session: AsyncSession):
        stmt = select(Booking).where(house_uid==Booking.house_uid)

        result = await session.exec(stmt)

        house = await house_service.get_house_by_id(house_uid, session)
        if user_id==house.user_uid:

            return result.first()
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "message": "You're not the owner of the house"
                }
            )
    async def cancel_booking(self, booking_uid: str, session: AsyncSession):
        booking = await self.get_specific_booking(booking_uid, session)
        
        house = await house_service.get_house_by_id(booking.house_uid, session)
        if house.Available==True:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="The shortlet booking you're trying to cancel isn't booked"
                )
        house.Available = True
        booking.status="canceled"
        booking.expires_at = None
        
        session.delete(booking)

        session.refresh(booking)
        await session.commit()
        return JSONResponse(
                status_code=status.HTTP_200_OK,
                content= {
                    "message": "The shortlet you booked has been canceled",
                    "House Availability": house.Available
                }
            )
        
    async def get_bookings_ending_at(self, date: datetime, session: AsyncSession):
        stmt = select(Booking).where(func.date(Booking.end_date) <= date.date())
        result = await session.exec(stmt)
        return result.all()
    
    async def get_bookings_starting_at(self, date: datetime, session: AsyncSession):
        stmt = select(Booking).where(Booking.start_date <= date)

        result = await session.exec(stmt)

        return result.all()    
    
    async def end_booking(self, date: datetime, session: AsyncSession):
        bookings = await self.get_bookings_ending_at(date, session)

        for booking in bookings:
            user = await user_service.get_user_by_id(booking.user_uid, session)
            house = await house_service.get_house_by_id(booking.house_uid, session)
            host = await user_service.get_user_by_id(house.user_uid, session)
            print(house)
            user_message = create_message(
                recipients=[user.email],
                subject="Your Booking Has Ended",
                body=f"<h2>Your booking for house '{house.title}' has ended.</h2>"
            )
            host_message = create_message(
                recipients=[host.email],
                subject="The Booking of your house has Ended",
                body=f"<h2>The booking for your house '{house.title}' has ended.</h2>"
            )

            await mails.send_message(user_message)
            await mails.send_message(host_message)

            house.Available = True
            session.add(house)
            await session.commit()
            return date.date()