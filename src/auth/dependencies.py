from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer
from fastapi.security.http import HTTPAuthorizationCredentials
from sqlmodel.ext.asyncio.session import AsyncSession 
from typing import List
from .utils import decode_token
from src.db.redis import token_in_blocklist
from src.db.main import get_session
from .service import UserService
from src.db.models import User
# from src.errors import (
#     InvalidTokenError,
#     RefreshTokenRequiredError,
#     AccountNotVerified,
#     AccessTokenRequiredError,
#     RevokedTokenError,
#     InsufficientPermission
# )

user_service = UserService()

class TokenBearer(HTTPBearer):
    def __init__(self, auto_error =True):
        super().__init__(auto_error=auto_error)

    async def __call__(self, request: Request) -> HTTPAuthorizationCredentials:
        creds = await super().__call__(request)

        token = creds.credentials

        if not self.token_valid:
          ...  # raise InvalidTokenError()
        token_data = decode_token(token)

        if await token_in_blocklist(token_data["jti"]):
            # raise RevokedTokenError()
            ...
        
        self.verify_token_data(token_data)

        return token_data
    
    def verify_token_data(self, token_data:dict) -> None:
        raise NotImplementedError("Please Override this method in child classes")
    
    def token_valid(self, token: str) -> bool:

        token_data = decode_token(token)
        
        return True if token_data is not None else False


class AccessTokenBearer(TokenBearer):
    
    def verify_token_data(self, token_data:dict) -> None:
        if token_data and token_data.get("refresh", False):
            # raise AccessTokenRequiredError()
            ...

class RefreshTokenBearer(TokenBearer):
    def verify_token_data(self, token_data:dict) -> None:
        if token_data and not token_data.get("refresh", False):
            # raise RefreshTokenRequiredError()
            ...

async def get_current_user(
        token_detail: dict= Depends(AccessTokenBearer()),
        session: AsyncSession= Depends(get_session)
):
    user_email = token_detail["user"]["email"]

    user = await user_service.get_user_by_email(user_email, session)

    return user


class RoleChecker:
    def __init__(self, allowed_roles: List[str]) -> None:
        
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: User= Depends(get_current_user)) -> any:
        if not current_user.is_verified:
            # raise AccountNotVerified()
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account not verified"
            )
        if current_user.role in self.allowed_roles:
            return True
          
        # raise InsufficientPermission()
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this route"
        )