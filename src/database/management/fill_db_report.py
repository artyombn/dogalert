import argparse
import asyncio
import random

from sqlalchemy.ext.asyncio import AsyncSession

from src.config.config import settings
from src.database.models.base_model import async_session_maker
from src.schemas.report import ReportCreate
from src.services.pet_service import PetServices
from src.services.report_service import ReportServices
from src.services.user_service import UserServices

faker = settings.get_faker()


async def create_reports(count: int, session: AsyncSession) -> list[tuple[ReportCreate, int, int]]:
    reports = []

    users_uids = await UserServices.get_all_users_uids(session)
    pets_uids = await PetServices.get_all_pet_uids(session)

    if count > len(pets_uids):
        raise ValueError("Not enough pets to generate reports")

    sampled_pets = random.sample(pets_uids, count)

    for pet_id in sampled_pets:
        user_id = random.choice(users_uids)

        report = ReportCreate(
            title=faker.sentence(nb_words=5)[:50],
            content=faker.text(max_nb_chars=300),
            location=faker.city(),
            region=faker.region(),
        )

        reports.append((report, user_id, pet_id))

    return reports


async def fill_db_report(
        report_data: ReportCreate,
        user_id: int,
        pet_id: int,
        session: AsyncSession,
) -> None:

    await ReportServices.create_report(
        report_data,
        user_id,
        pet_id,
        session,
    )

async def main(count: int) -> None:
    async with async_session_maker() as session:
        reports = await create_reports(count, session)
        for report, user_id, pet_id in reports:
            await fill_db_report(report, user_id, pet_id, session)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fill db with fake reports")
    parser.add_argument(
        "-count",
        type=int,
        default=5,
        help="Number of reports to create",
    )
    args = parser.parse_args()

    asyncio.run(main(args.count))


