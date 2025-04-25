import argparse
import asyncio
import random

from sqlalchemy.ext.asyncio import AsyncSession

from src.database.management.pet_data import pet_data
from src.database.models.base_model import async_session_maker
from src.schemas.pet import PetCreate, PetPhotoCreate
from src.services.pet_photo_service import PetPhotoServices
from src.services.pet_service import PetServices
from src.services.user_service import UserServices


def create_pets(count: int) -> list[PetCreate]:
    pets = []

    for i in range(count):
        pet = PetCreate(
            name=random.choice(pet_data.pet_names),
            breed=random.choice(pet_data.pet_breeds),
            age=random.choice(list(range(1, 21))),
            color=random.choice(pet_data.pet_colors),
            description=random.choice(pet_data.pet_descriptions),
        )

        pets.append(pet)

    return pets


async def fill_db_pet_with_photo(
        pet_data: PetCreate,
        photo_data: PetPhotoCreate,
        session: AsyncSession,
) -> None:
    users = await UserServices.get_all_users(session)
    owner_id = (random.choice(users)).id

    new_pet = await PetServices.create_pet(
        owner_id,
        pet_data,
        session,
    )

    if new_pet is None:
        return

    await PetPhotoServices.create_pet_photo(new_pet.id, photo_data, session)

def create_pets_photos(count: int) -> list[PetPhotoCreate]:
    pets_photos = []

    for i in range(count):
        pet_photo = PetPhotoCreate(
            url=(random.choice(pet_data.pet_photos_links))["url"],
        )

        pets_photos.append(pet_photo)

    return pets_photos

async def main(count: int) -> None:
    pets = create_pets(count)
    pets_photos = create_pets_photos(count)

    tasks = []
    for pet, pet_photo in zip(pets, pets_photos):
        async def task(p: PetCreate = pet, ph: PetPhotoCreate = pet_photo) -> None:
            async with async_session_maker() as session:
                await fill_db_pet_with_photo(p, ph, session)
        tasks.append(task())
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fill db with fake pets")
    parser.add_argument(
        "-count",
        type=int,
        default=5,
        help="Number of pets to create",
    )
    args = parser.parse_args()

    asyncio.run(main(args.count))


