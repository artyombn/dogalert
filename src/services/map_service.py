import logging

from fastapi import HTTPException
from geoalchemy2 import WKTElement
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import Lake
from src.schemas.map import MapCreate, Map

logger = logging.getLogger(__name__)


class MapServices:
    @classmethod
    async def create_lake(
            cls,
            map_data: MapCreate,
            session: AsyncSession,
    ) -> Map | None:
        data_dict = map_data.model_dump(exclude_unset=True)

        lake_data = {
            "name": data_dict.get("name")
        }

        fake_lake = Lake(**lake_data)

        if isinstance(data_dict.get("geom"), str):
            fake_lake.geom = WKTElement(data_dict.get("geom"), srid=4326)

        session.add(fake_lake)
        try:
            await session.commit()
            await session.refresh(fake_lake)
        except Exception as e:
            await session.rollback()
            raise HTTPException(status_code=422, detail=f"Failed to create Lake: {str(e)}")

        query = select(
            Lake.id,
            Lake.name,
            func.ST_AsText(Lake.geom).label("geom")
        ).filter(Lake.id == fake_lake.id)

        result = await session.execute(query)
        row = result.first()

        if row:
            return Map(**row._asdict())
        return None

    @classmethod
    async def get_lake(
            cls,
            id: int,
            session: AsyncSession,
    ) -> Lake | None:
        query = select(
            Lake.id,
            Lake.name,
            func.ST_AsText(Lake.geom).label("geom")
        ).filter_by(id=id)
        lake_result = await session.execute(query)
        row = lake_result.first()
        if row:
            return Map(**row._asdict())
        return None
