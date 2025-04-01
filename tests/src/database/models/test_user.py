from sqlalchemy.future import select

from src.database.models.user import User
from .db_fixture import db_session, db_fill_data


async def test_create_user(db_session, db_fill_data):
    user = db_fill_data["user"]

    stmt = select(User).where(User.username == "artyombn")
    result = await db_session.execute(stmt)
    is_user = result.scalar_one()

    assert is_user is not None
    assert is_user.telegram_id == user.telegram_id
    assert is_user.username == "artyombn"
    assert is_user.first_name == "Artem"
    assert is_user.phone == None
    assert is_user.pets == user.pets and is_user.pets[0].name == "Douglas"
    assert is_user.reports == user.reports and is_user.reports[0].title == "Douglas lost"