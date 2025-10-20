from fastapi import APIRouter, Depends, HTTPException, status, UploadFile
from sqlmodel.ext.asyncio.session import AsyncSession
import tempfile
import aiofiles
from src.auth.dependencies import AccessTokenBearer, RoleChecker, get_current_user
from src.houses.schema import HouseCreateModel, HouseUpdateModel
from src.db.main import get_session
from src.houses.service import HouseService
from src.b2 import b2_upload_file


house_router = APIRouter()
house_service = HouseService()
CHUNK_SIZE = 1024*1024

@house_router.get("/")
async def get_houses(session: AsyncSession= Depends(get_session), token: str= Depends(AccessTokenBearer())):
    houses = await house_service.get_all_houses(session)

    return houses

@house_router.get("/{uid}")
async def get_particular_house_by_uid(uid: str, session: AsyncSession= Depends(get_session),
                                       token: dict= Depends(AccessTokenBearer())):
    house = await house_service.get_house_by_id(uid, session)

    return house

@house_router.get("/{address}")
async def get_particular_house_by_address(address: str, session: AsyncSession= Depends(get_session),
                                           token: dict= Depends(AccessTokenBearer())):
    house = await house_service.get_house_by_address(address, session)

    return house
#### need to do the aws or b2 side
@house_router.post("/create")
async def create_house(file: UploadFile, house_model: HouseCreateModel= Depends(HouseCreateModel.as_form),
                        session: AsyncSession= Depends(get_session), token_details: dict= Depends(AccessTokenBearer()),
                          _: bool= Depends(RoleChecker(["host", "admin"]))):
    try: 
        filename = tempfile.mktemp()
        async with aiofiles.open(filename, "wb") as f:
            while chunk:= await file.read(CHUNK_SIZE):
                await f.write(chunk)
        file_url = b2_upload_file(filename, file.filename)
        house_model.house_image_url = file_url

        user_uid = token_details.get("user")["id"]
        house = await house_service.add_house(house_model,user_uid, session)

        if house is not None:
            return house
        
        else:
            raise HTTPException(
                status_code = status.HTTP_400_BAD_REQUEST,
                detail = "Something went wrong"
            )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"There was an error loading the file, {e}"
        )
    
@house_router.post("/search-house")
async def search(    address: str | None = None,
    price_min: float | None = None,
    price_max: float | None = None,
    state: str | None = None,
    bedroom: int | None = None,
    bathroom: int | None = None,

    session: AsyncSession= Depends(get_session), token_details: dict= Depends(AccessTokenBearer())):

    values = { "address": address, "price_min": price_min, "price_max": price_max, "state": state, "bedroom": bedroom, "bathroom": bathroom }
    stmt = await house_service.search_houses(values, session)
    
    return stmt

@house_router.post("/update/{house_uid}")
async def update_house(house_uid: str, house_model: HouseUpdateModel, session: AsyncSession= Depends(get_session),
                                       token: dict= Depends(AccessTokenBearer()),  _: bool= Depends(RoleChecker(["host", "admin"]))):
    house = await house_service.get_house_by_id(house_uid, session)
    if house:
        result = await house_service.update_house(house, house_model, session)

        return result
    else:
        raise HTTPException(
            status_code= status.HTTP_404_NOT_FOUND,
            detail= "House doesn't exist"
        )

@house_router.delete("/delete/{house_uid}")
async def delete_house(
    house_uid: str, session: AsyncSession= Depends(get_session),
        token_details: dict= Depends(AccessTokenBearer()), _: bool= Depends(RoleChecker(["host", "admin"]))):
    
    result = await house_service.delete_house(house_uid, session)

    return result if not None else None