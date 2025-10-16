from pydantic import BaseModel
from datetime import datetime
from typing import Optional
import uuid 

class BookingModel(BaseModel):
    booking_uid: uuid.UUID 
    house_uid: uuid.UUID 
    user_uid: uuid.UUID 
    start_date: datetime
    end_date: datetime
    expires_at: datetime
    amount_cents: int
    status: str
    expires_at: Optional[datetime]
    stripe_session_id: Optional[str]

class BookingCreateModel(BaseModel):
    house_uid: str
    user_uid: str
    start_date: datetime
    end_date: datetime