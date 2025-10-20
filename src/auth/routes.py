from fastapi import APIRouter, Depends, status, BackgroundTasks
from fastapi.exceptions import HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi.responses import JSONResponse
from datetime import timedelta
from typing import List
from .schema import (UserCreateModel, UserLoginModel, UserModel,
                     UserUpdateModel, EmailModel, ResetPasswordModel,
                     RoleUpdateModel)
from .service import UserService
from .utils import create_url_safe_token, verify_password, create_access_token, decode_url_safe_token, hash_password
from .dependencies import RoleChecker, get_current_user, AccessTokenBearer, RefreshTokenBearer
from src.db.main import get_session
from src.db.redis import add_jti_to_blocklist
from src.config import Config
from src.db.models import User
from src.mail.mail import create_message, mails

auth_router = APIRouter()
user_service = UserService()
REFRESH_TOKEN_EXPIRY_TIME = 7
# role_checker = RoleChecker(["user", "admin"])

@auth_router.get("/users", response_model=List[UserModel]) #only accessible by admins
async def get_all_users(_:bool= Depends(RoleChecker(["admin"])) ,session: AsyncSession= Depends(get_session)):
    users = await user_service.get_users(session)

    if users is not None:
        return users
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Smth went wrong"
    )

@auth_router.post("/signup")
async def create_user(user_model: UserCreateModel, background_tasks: BackgroundTasks, session: AsyncSession= Depends(get_session)):
    user_exists = await user_service.user_exists(email=user_model.email,session=session)

    if user_exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with that email already exists"
        )
    
    else:
        user = await user_service.create_user(user_model, session)

        token = create_url_safe_token({'email': user.email})

        link = f"http://{Config.DOMAIN}/api/v1/auth/verify/{token}"
        html_message = f"""
        <h1>Verify your email</h1>
        <p> Please click the link below to verify your email address:</p>
        <a href="{link}">Verify Email</a>
        """
        message = create_message(
            subject="Welcome to Shortlet",
            recipients=[user_model.email],
            body=html_message
        )
        background_tasks.add_task(mails.send_message, message)

        return {
            "message": "Account Created! Check email to verify your account",
            "user": user
        }

@auth_router.get("/verify/{token}")
async def verify_email(token: str, session: AsyncSession= Depends(get_session)):
    token_data = decode_url_safe_token(token)

    email = token_data.get("email")
    user = await user_service.get_user_by_email(email, session)
    if user is not None:
        print(user)
        await user_service.update_user(user, {"is_verified": True}, session)
        return JSONResponse(
            content={
               "message": "Email verified successfully"
            },
            status_code=status.HTTP_200_OK
         )
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Invalid token or user does not exist"
    )


@auth_router.post("/login")
async def login_user(user_model: UserLoginModel, session: AsyncSession= Depends(get_session)):
    user = await user_service.get_user_by_email(user_model.email, session)
    print(user)

    password = user_model.password
    hash_password = user.password

    if user is not None:
        password_valid = verify_password(password, hash_password)
    if password_valid:
        access_token = create_access_token(
            user_data={
                "id": str(user.uid),
                "email": user.email,
                "role": user.role
            }
        )

        refresh_token = create_access_token(
            user_data={
                "id": str(user.uid),
                "email": user.email,
                "role": user.role
            },
            refresh=True,
            expiry_time=timedelta(days=REFRESH_TOKEN_EXPIRY_TIME)
        )
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Login Successful",
                "access_token": access_token,
                "refresh_token": refresh_token,
                "user": {
                  "email": user.email,
                  "uid": str(user.uid)
               }
            }
        )
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid email or password"
    )

@auth_router.get("/me", response_model=UserModel)
async def get_user_details(current_user: UserModel= Depends(get_current_user), _: bool=Depends(RoleChecker(["admin", "user"]))):
    return current_user

@auth_router.post("/update_profile")
async def update_profile(user_model: UserUpdateModel, session: AsyncSession= Depends(get_session), token:str= AccessTokenBearer(), user: User= Depends(get_current_user), _: bool= Depends(RoleChecker(["admin", "user"]))):
    # present_user = user_service.get_user_by_email(user., session)
    if user is not None:
        updated_user = user_service.update_user(user, user_model, session)

        return updated_user
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "message": "user not found"
            }
        )

@auth_router.get("/logout")
async def revoke_token(token_detail: dict= Depends(AccessTokenBearer())):
    jti = token_detail["jti"]

    add_jti_to_blocklist(jti)

    return JSONResponse(
      content={
         "Message": "logged out Successfully"
      },
      status_code=status.HTTP_200_OK
   )

@auth_router.post("/forgot_password")
async def forgot_password(model: EmailModel, background_tasks: BackgroundTasks, session: AsyncSession= Depends(get_session)):
    email = model.email

    user_exist = await user_service.user_exists(email, session)
    if not user_exist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "message": "User with email does not exist"
            }
        )
    else:
        user = await    user_service.get_user_by_email(email, session)

        token = create_url_safe_token({"email": email})

        link = f"http://{Config.DOMAIN}/api/v1/auth/reset_password/{token}"
        html_message = f"""
        <h1>Forgot Password</h1>
        <p> Please click the link below to create new password:</p>
        <a href="{link}">Reset password</a>
        """
        message = create_message(
            subject="Welcome to Shortlet",
                recipients=[email],
                body=html_message
        )
        background_tasks.add_task(mails.send_message, message)

        return {
            "message":"Check email to reset your password",
        }
    
@auth_router.post("/reset_password/{token}")
async def reset_password(token: str, model: ResetPasswordModel, session: AsyncSession= Depends(get_session)):
    token_data = decode_url_safe_token(token)

    email = token_data.get("email")
    user = await user_service.get_user_by_email(email, session)
    if user is not None:
        hashed_password = hash_password(model.new_password)
        await user_service.update_user(user, {"password": hashed_password}, session)
        return JSONResponse(
            content={
               "message": "Password reset successfully"
            },
            status_code=status.HTTP_200_OK
         )
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Invalid token or user does not exist"
    )

@auth_router.post("/refresh")
async def refresh_token(token_detail: dict= Depends(RefreshTokenBearer())):
    if token_detail.get("refresh"):
        new_access_token = create_access_token(
            user_data={
                "id": token_detail.get("id"),
                "email": token_detail.get("email"),
                "role": token_detail.get("role")
            }
        )
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "access_token": new_access_token
            }
        )
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid refresh token"
    )

@auth_router.post("/update_role")
async def register_as_a_host(model: RoleUpdateModel, session: AsyncSession= Depends(get_session), token:dict=Depends(AccessTokenBearer()), user: User= Depends(get_current_user), _: bool=Depends(RoleChecker(["admin", "user"]))):
    if user is not None:
        if user.role == "host":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "message": "You are already registered as a host"
                }
            )
        password_valid = verify_password(model.password, user.password)
        if not password_valid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "message": "Invalid password"
                }
            )
        updated_user = await user_service.update_user(user, {"role": "host"}, session)

        return {
            "message": "You are now registered as a host",
            "user": updated_user
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "message": "user not found"
            }
        )