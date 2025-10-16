from pydantic import BaseModel
from datetime import datetime
from typing import Optional
import uuid

class ReviewModel(BaseModel):
    uid: uuid.UUID
    review_text: str
    rating: float
    house_uid: Optional[uuid.UUID]
    user_uid: Optional[uuid.UUID]
    created_at: datetime
    updated_at: datetime

class ReviewCreateModel(BaseModel):
    review_text: str
    rating: float