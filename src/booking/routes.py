from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks
from sqlmodel.ext.asyncio.session import AsyncSession
from starlette.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse
import stripe
from src.booking.service import BookingService
from src.booking.schema import BookingModel, BookingCreateModel
from src.auth.dependencies import AccessTokenBearer, get_current_user, RoleChecker
from src.db.models import User
from src.auth.service import UserService
from src.houses.service import HouseService
from src.config import Config
from src.auth.utils import to_naive_utc
from src.mail.mail import create_message, mails
from src.db.main import get_session

stripe.api_key = Config.STRIPE_SECRET_KEY
booking_router = APIRouter()
house_service = HouseService()
user_service = UserService()
booking_service = BookingService()
CURRENCY = "NGN"

@booking_router.get("/get_all_bookings")
async def get_all_bookings(session: AsyncSession= Depends(get_session),
                                             token_details: dict= Depends(AccessTokenBearer()), _: bool= Depends(RoleChecker(["admin"]))):
    bookings = await booking_service.get_all_bookings(session)

    if bookings is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Something went wrong"
        )
    return bookings

@booking_router.post("/book_house", status_code=status.HTTP_201_CREATED)
async def book_house( booking_model: BookingCreateModel,
     current_user: User= Depends(get_current_user), session: AsyncSession = Depends(get_session)
):
    booking_model.user_uid = current_user.uid
    user_email = current_user.email
    house = await house_service.get_house_by_id(booking_model.house_uid, session)
    host_uid = house.user_uid

    host_user = await user_service.get_user_by_id(host_uid, session)
    host_email = host_user.email

    booking_model.start_date = to_naive_utc(booking_model.start_date)
    booking_model.end_date = to_naive_utc(booking_model.end_date)
    booking = await booking_service.book_house(booking_model, session)
    if not booking:
        raise HTTPException(status_code=400, detail="Booking failed, House is already booked for the selected dates")
    def _create_session():
        return stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[
                {
                    "price_data":{
                        "currency": CURRENCY,
                        "product_data": {"name": f"Booking: {house.title}"},
                        "unit_amount": int(booking.amount*100)
                    },
                    "quantity": 1
                }],
                mode="payment",
                success_url=f"{Config.SUCCESS_URL}?session_id={{CHECKOUT_SESSION_ID}}",
                cancel_url=Config.CANCEL_URL,
                metadata={"booking_uid": str(booking.booking_uid)},
                customer_email=user_email
        )
    stripe_session = await run_in_threadpool(_create_session)
    booking.stripe_session_id = stripe_session.id
    booking.stripe_payment_intent = stripe_session.payment_intent
    await session.commit()
    # message = create_message(
    #     subject="Booking Confirmation",
    #     recipients=[user_email],  
    #     body=f"<h2>Your booking for house {house.title} with id {booking_model.house_uid} from {booking_model.start_date} to {booking_model.end_date} is confirmed.</h2>"
    # )
    # host_message = create_message(
    #     subject="Your House Was Booked",
    #     recipients=[host_email],
    #     body=f"<h2>Your house '{house.title}' was booked from {booking_model.start_date} to {booking_model.end_date}.</h2>"
    # )
    # await mails.send_message(host_message)
    # await mails.send_message(message)
    return {
        "booking_id": booking.booking_uid,
        "stripe_session_id": stripe_session.id,
        "checkout_url": stripe_session.url
    }

@booking_router.post("/webhook")
async def stripe_webhook(request: Request, session: AsyncSession= Depends(get_session)):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = await run_in_threadpool(stripe.Webhook.construct_event, payload, sig_header, Config.STRIPE_WEBHOOK_SECRET)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Webhook error: {e}")
    if event.type == "checkout.session.completed":
        session_obj = event["data"]["object"]
        booking_id = session_obj["metadata"]["booking_uid"]
        payment_intent = session_obj["payment_intent"]

        booking = await booking_service.get_specific_booking(booking_id, session)
        if not booking:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "Booking not found"}
            )
        if booking.status!="paid":
            booking.status="paid"
            booking.expires_at = None
            booking.stripe_payment_intent = payment_intent
            house = await house_service.get_house_by_id(booking.house_uid, session)
            user = await user_service.get_user_by_id(booking.user_uid, session)
            host_uid = house.user_uid
            host = await user_service.get_user_by_id(host_uid, session)
            host_email = host.email
            user_email = user.email
            message = create_message(
                subject="Booking Confirmation",
                recipients=[user_email],  
                body=f"<h2>Your booking for house {house.title} with id {booking.house_uid} from {booking.start_date} to {booking.end_date} is confirmed.</h2>"
            )
            host_message = create_message(
                subject="Your House Was Booked",
                recipients=[host_email],
                body=f"<h2>Your house '{house.title}' was booked from {booking.start_date} to {booking.end_date}.</h2>"
            )
            await mails.send_message(host_message)
            await mails.send_message(message)

    elif event.type == "checkout.session.expired":
        session_obj = event["data"]["object"]
        booking_id = session_obj["metadata"]["booking_uid"]

        booking = await booking_service.get_specific_booking(booking_id, session)
        if not booking:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "Booking not found"}
            )
        if booking.status!="paid":
            await booking_service.cancel_booking(booking_id, session)
            user = await user_service.get_user_by_id(booking.user_uid, session)
            message = create_message(
                subject="Booking Expired",
                recipients=[user.email],
                body=f"<h2>Your booking for house with id {booking.house_uid} from {booking.start_date} to {booking.end_date} has expired. Payment Failed.</h2>"
            )
            await mails.send_message(message)
    return JSONResponse({
        "received": True
    })

@booking_router.get("/{booking_uid}")
async def get_details_of_a_specific_booking(booking_uid: str, session: AsyncSession= Depends(get_session),
                                             token_details: dict= Depends(AccessTokenBearer())):
    booking_detail = await booking_service.get_details_specific_booking(booking_uid, session)
    if not booking_detail:
        raise HTTPException(status_code=400, detail="getting details of the booking failed")
    return booking_detail

@booking_router.get("/booking_history/{user_uid}")
async def get_users_booking_history(user_uid: str, session: AsyncSession= Depends(get_session),
                                             token_details: dict= Depends(AccessTokenBearer()),
                                             current_user: User= Depends(get_current_user)):
    user_uid = current_user.uid
    booking_history = await booking_service.get_users_booking_history(user_uid, session)

    if booking_history:
        return booking_history
    raise HTTPException(status_code=400, detail="getting user Booking history failed")

@booking_router.get("/house/{house_uid}")
async def get_all_bookings_for_a_house(house_uid: str, session: AsyncSession= Depends(get_session),
                                       current_user: User= Depends(get_current_user),
                                             token_details: dict= Depends(AccessTokenBearer()), _: bool= Depends(RoleChecker(["host", "admin"]))):
    user_uid  = current_user.uid
    booking_history = await booking_service.get_all_booking_for_house(house_uid, user_uid, session)

    if booking_history:
        return booking_history
    raise HTTPException(status_code=400, detail="Booking failed")

@booking_router.delete("/{booking_uid}")
async def cancel_booking(booking_uid: str, session: AsyncSession= Depends(get_session),
                                             token_details: dict= Depends(AccessTokenBearer()), _: bool= Depends(RoleChecker(["user", "admin"]))):
    detail = await booking_service.cancel_booking(booking_uid, session)
    if not detail:
        raise HTTPException(status_code=400, detail="getting details of the booking failed")
    return detail

