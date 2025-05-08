import argparse
import asyncio
import random

from pydantic_extra_types.phone_numbers import PhoneNumber
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.config import settings
from src.database.models.base_model import async_session_maker
from src.schemas.user import UserCreate
from src.services.user_service import UserServices

faker = settings.get_faker()

def generate_valid_russian_phone() -> PhoneNumber:
    valid_prefixes = ["79"]
    prefix = faker.random.choice(valid_prefixes)
    return PhoneNumber(f"+{prefix}{faker.numerify('#########')}")

def create_users(count: int) -> list[UserCreate]:
    users = []

    for i in range(count):
        user = UserCreate(
            username=faker.user_name(),
            first_name=faker.first_name(),
            last_name=faker.last_name(),
            phone=generate_valid_russian_phone(),
            agreement=False,
        )

        users.append(user)

    return users


async def fill_db_user(
        user_data: UserCreate,
        session: AsyncSession,
) -> None:
    telegram_id = random.choice(range(10000))
    await UserServices.create_user(
        user_data,
        session,
        telegram_id,
    )

async def main(count: int) -> None:
    users = create_users(count)

    tasks = []
    for user in users:
        async def task(u: UserCreate = user) -> None:
            async with async_session_maker() as session:
                await fill_db_user(u, session)
        tasks.append(task())
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fill db with fake users")
    parser.add_argument(
        "-count",
        type=int,
        default=5,
        help="Number of users to create",
    )
    args = parser.parse_args()

    asyncio.run(main(args.count))


