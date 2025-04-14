from sqlalchemy.ext.asyncio import AsyncSession
from src.database.models.base_model import async_session_maker


async def get_async_session() -> AsyncSession:
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.rollback()