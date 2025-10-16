from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from fastapi import Form
import uuid

class HouseModel(BaseModel):
    house_uid: uuid.UUID
    title: str
    address: str
    state: str
    bedroom: int
    bathroom: int
    price_per_night: float
    description: str
    Available: bool = True
    user_uid: uuid.UUID
    created_at: datetime

class HouseCreateModel(BaseModel):
    title: str
    address: str
    state: str
    bedroom: int
    bathroom: int
    price_per_night: float
    description: str
    available: bool
    house_image_url: Optional[str] = None

    @classmethod
    def as_form(
        cls,
        title: str = Form(...),
        address: str = Form(...),
        state: str = Form(...),
        bedroom: int = Form(...),
        bathroom: int = Form(...),
        price_per_night: float = Form(...),
        description: str = Form(...),
        available: bool = Form(...),
    ):
        return cls(
            title=title,
            address=address,
            state=state,
            bedroom=bedroom,
            bathroom=bathroom,
            price_per_night=price_per_night,
            description=description,
            available=available
        )

class HouseUpdateModel(BaseModel):
    title: Optional[str]
    address: Optional[str]
    price_per_night: Optional[float]
    description: Optional[str]
    Available: Optional[bool]