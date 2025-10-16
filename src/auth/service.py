from sqlmodel import select, desc
from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi.exceptions import HTTPException
from .utils import hash_password
from src.db.models import User
from .schema import UserCreateModel

class UserService:
    async def get_user_by_email(self,email:str, session: AsyncSession):
        statement = select(User).where(User.email==email)
        
        result = await session.exec(statement)
        user = result.first()
    
        return user if user is not None else "something went wrong"

    async def get_user_by_id(self,uid:str, session: AsyncSession):
        statement = select(User).where(User.uid==uid)
        
        result = await session.exec(statement)
        user = result.first()
    
        return user

    async def get_users(self, session: AsyncSession):
        stmt = select(User).order_by(desc(User.created_at))

        result = await session.exec(stmt)
        users = result.all()

        return users
    
    async def user_exists(self, email: str, session: AsyncSession):
        user = await self.get_user_by_email(email, session)

        return True if user is not None else False
    
    async def create_user(self, user_model: UserCreateModel, session: AsyncSession):
        user_data = user_model.model_dump()

        new_user = User(
            **user_data
        )
        new_user.password = hash_password(user_data["password"])

        session.add(new_user)
        await session.commit()

        return new_user
    
    async def update_user(self, user: User, user_data: dict, session: AsyncSession):

        for key, value in user_data.items():
            setattr(user, key, value)

        await session.commit()

        return user
    

