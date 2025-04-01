import pytest

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from src.database.models.base_model import Base
from src.database.models.user import User
from src.database.models.report import Report
from src.database.models.pet import Pet

DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest.fixture(scope="function")
async def db_session():
    engine = create_async_engine(url=DATABASE_URL)
    async_session_factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        autocommit=False,
        autoflush=False,
        expire_on_commit=False,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_factory() as session:
        yield session

    await engine.dispose()

@pytest.fixture(scope="function")
async def db_fill_data(db_session: AsyncSession):
    user = User(
        telegram_id=1234567890,
        username="artyombn",
        first_name="Artem",
    )
    pet = Pet(name="Douglas")
    report = Report(
        title="Douglas lost",
        content="Help to find Douglas!",
        user=user,
        pet=pet,
    )

    pet.owners.append(user)
    pet.reports.append(report)

    db_session.add_all([user, pet, report])
    await db_session.commit()

    return {"user": user, "pet": pet, "report": report}
