from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from itsdangerous import URLSafeTimedSerializer
import logging
import uuid
import jwt
from src.config import Config

pwd_context = CryptContext(schemes=["bcrypt"])
auth_s = URLSafeTimedSerializer(
    secret_key=Config.SECRET_KEY,
    salt="email-verification"
)
ACCESS_TOKEN_EXPIRY_TIME = 3600

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(password: str, hash_password: str) -> bool:
    return pwd_context.verify(password, hash_password)

def create_access_token(user_data: dict, refresh:bool = False, expiry_time:timedelta = None):
    payload = {}

    expire = datetime.now(timezone.utc) + (expiry_time if expiry_time is not None else timedelta(seconds=ACCESS_TOKEN_EXPIRY_TIME))

    payload["user"] = user_data
    payload["jti"] = str(uuid.uuid4())
    payload["refresh"] = refresh
    payload["exp"] = expire.timestamp()

    token = jwt.encode(
        payload=payload,
        key=Config.SECRET_KEY,
        algorithm=Config.ALGORITHM
    )

    return token

def decode_token(token: str):
    try:
        token_data = jwt.decode(
            jwt=token,
            key=Config.SECRET_KEY,
            algorithms=Config.ALGORITHM
        )
        return token_data
    except jwt.PyJWKError as e:
        logging.error(e)

def create_url_safe_token(user_data: dict) -> str:
    token = auth_s.dumps(user_data)

    return token

def decode_url_safe_token(token: str) -> dict:
    try:
        token_data = auth_s.loads(token)
        return token_data
    except Exception as e:
        logging.error(e)

def to_naive_utc(dt: datetime) -> datetime:
    if dt.tzinfo is not None:
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt

def nights_in_between(start_date: datetime, end_date: datetime) -> int:
    delta = end_date - start_date
    nights = delta.days
    return max(1, nights)
