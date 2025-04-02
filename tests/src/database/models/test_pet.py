from sqlalchemy.future import select

from src.database.models.pet import Pet
from .db_fixture import db_session, db_fill_data


async def test_create_pet(db_session, db_fill_data):
    pet = db_fill_data["pet"]

    stmt = select(Pet).where(Pet.name == "Douglas")
    result = await db_session.execute(stmt)
    is_pet = result.scalar_one()

    assert is_pet is not None
    assert is_pet.name == pet.name
    assert is_pet.breed == None
    assert is_pet.owners == pet.owners and is_pet.owners[0].username == "artyombn"
    assert is_pet.reports == pet.reports and is_pet.reports[0].title == "Douglas lost"
