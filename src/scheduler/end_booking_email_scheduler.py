from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime
from src.db.main import get_session
from src.booking.service import BookingService

scheduler = AsyncIOScheduler()

async def send_end_booking_emails():
    session_gen = get_session()
    session = await anext(session_gen)
    try:
        booking_service = BookingService()
        now = datetime.now()
        bookings = await booking_service.end_booking(now, session)
    finally:
        await session.close()

def start_scheduler():
    scheduler.add_job(send_end_booking_emails, "interval", minutes=720)
    scheduler.start()
