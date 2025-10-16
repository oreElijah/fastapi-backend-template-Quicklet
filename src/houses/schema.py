from pydantic import BaseModel
from datetime import datetime
from typing import Optional
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
    price_per_night: float
    description: str
    Available: bool

class HouseUpdateModel(BaseModel):
    title: Optional[str]
    address: Optional[str]
    price_per_night: Optional[float]
    description: Optional[str]
    Available: Optional[bool]