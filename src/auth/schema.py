from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import uuid

class UserModel(BaseModel):
    uid: uuid.UUID
    firstname: str
    lastname: str
    username: str
    email: str
    role: str
    is_verified: bool = False
    password: str
    created_at: datetime
    updated_at: datetime

class UserCreateModel(BaseModel):
    firstname: str
    lastname: str
    username: str
    email: str
    password: str
    # role: str = "user"

class UserUpdateModel(BaseModel):
    firstname: Optional[str]
    lastname: Optional[str]
    email: Optional[str]
    password: Optional[str]

class RoleUpdateModel(BaseModel):
    email: str
    password: str

class UserLoginModel(BaseModel):
    email: str
    password: str

class EmailModel(BaseModel):
    email: str

class ResetPasswordModel(BaseModel):
    new_password: str