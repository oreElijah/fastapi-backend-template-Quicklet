from sqlmodel import or_, select, desc
from sqlmodel.ext.asyncio.session import AsyncSession
from src.db.models import House
from src.houses.schema import HouseModel, HouseUpdateModel

class HouseService:
    async def get_all_houses(self, session: AsyncSession):
        stmt = select(House).order_by(desc(House.created_at))

        result = await session.exec(stmt)

        return result.all()
    
    async def get_house_by_address(self, address: str, session: AsyncSession):
        stmt = select(House).where(address==House.address)

        result = await session.exec(stmt)

        return result.first()
    
    async def get_house_by_id(self, uid: str, session: AsyncSession):
        stmt = select(House).where(uid==House.house_uid)

        result = await session.exec(stmt)

        return result.first()
    
    async def add_house(self, house: HouseModel,user_uid: str, session: AsyncSession):
        house_dict = house.model_dump()

        new_house = House(
            **house_dict
                      )

        new_house.user_uid = user_uid
        session.add(new_house)
        await session.commit()

        return new_house
    
    async def house_exists(self, address: str, session: AsyncSession):
        house = await self.get_house_by_address(address, session)

        return True if house is not None else False
    
    async def house_exists_by_uid(self, uid: str, session: AsyncSession):
        house = await self.get_house_by_id(uid, session)

        return True if house is not None else False

    async def delete_house(self, uid: str, session: AsyncSession):
        house = await self.get_house_by_id(uid, session)

        if house:
            session.delete(house)
            await session.commit()
        return house
    
    async def update_house(self, house: House, house_data: HouseUpdateModel, session: AsyncSession):
        house_data = house_data.model_dump(exclude_unset=True)
        for key, value in house_data.items():
            setattr(house, key, value)

        await session.commit()

        return house
    
    async def update_house_by_id(self,house_data:dict, house_uid:str, session: AsyncSession):
        house_to_update = await self.get_house_by_id(house_uid, session)

        if house_to_update is not None:
            for k, v in house_data.items():
                setattr(house_to_update, k, v)

            await session.commit()
            await session.refresh(house_to_update)
        return house_data

    async def search_houses(self, values: dict, session: AsyncSession):
        query = select(House).where(House.available == True)


        address = values.get("address")
        state = values.get("state")
        bedroom = values.get("bedroom")
        bathroom = values.get("bathroom")
        price_min = values.get("price_min")
        price_max = values.get("price_max")

        if address or state:
            query = query.where(
                or_(
                    House.address.ilike(f"%{address}%") if address else False,
                    House.state.ilike(f"%{state}%") if state else False,
                )
            )
        if bedroom:
            query = query.where(House.bedroom <= bedroom)
        if bathroom:
            query = query.where(House.bathroom >= bathroom)
        if price_min:
            query = query.where(House.price_per_night >= price_min)
        if price_max:
            query = query.where(House.price_per_night <= price_max)

        result = await session.exec(query)
        houses = result.all()

        return houses