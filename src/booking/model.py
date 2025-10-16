from sqlmodel import SQLModel, Field, Column
import sqlalchemy.dialects.postgresql as pg
import uuid
from datetime import datetime

class Booking(SQLModel, table=True):
    __tablename__="booking"
    booking_uid: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    house_uid: uuid.UUID = Field(foreign_key="houses.house_uid")
    user_uid: uuid.UUID = Field(foreign_key="Users.uid")
    start_date: datetime
    end_date: datetime
    status: str = Field(default="pending")
    amount: int# this is the amount that will be charged for the stay in total based on the amount of nights spent
    booked_at: datetime = Field(sa_column = Column(
        pg.TIMESTAMP,
        nullable=False,
        default=datetime.now()))
    expires_at: datetime = Field(sa_column = Column(
        pg.TIMESTAMP))
    stripe_session_id: str = Field(default=None, nullable=True)
    stripe_payment_intent: str = Field(default=None, nullable=True)

    
    def __repr__(self):
        return f"Your booking id is -> {self.booking_uid}"