import argparse
import asyncio
import random

from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models.base_model import async_session_maker
from src.schemas.pet import PetCreate
from src.services.pet_service import PetServices
from src.services.user_service import UserServices

pet_names = [
    "Барсик", "Мурка", "Рекс", "Боня", "Чарли", "Снежок", "Том", "Лаки", "Белка", "Стелла",
    "Шарик", "Граф", "Пушок", "Жуля", "Тиша", "Луна", "Марс", "Рада", "Дикси", "Феликс",
]

pet_breeds = [
    "Мейн-кун", "Британская короткошерстная", "Сибирская", "Лабрадор", "Бульдог",
    "Шотландская вислоухая", "Корги", "Доберман", "Чихуахуа", "Йоркширский терьер",
    "Акита-ину", "Ротвейлер", "Персидская кошка", "Такса", "Боксер", "Шарпей", "Хаски",
    "Сфинкс", "Русская голубая", "Далматин",
]


pet_colors = [
    "белый", "чёрный", "рыжий", "серый", "пятнистый", "коричневый", "золотистый", "шоколадный",
    "песочный", "кремовый", "серо-белый", "чёрно-белый", "рыже-белый", "мраморный", "пепельный",
    "бежевый", "тёмно-серый", "карамельный", "тёмно-коричневый", "триколор",
]

pet_descriptions = [
    "Очень ласковый и дружелюбный", "Обожает играть с мячиком", "Легко идёт на контакт",
    "Боится громких звуков, но быстро привыкает", "Идеален для семьи с детьми",
    "Тихий, аккуратный, хорошо воспитан", "Любит гулять на свежем воздухе",
    "Обожает вкусняшки и мягкие пледы", "Очень умный и быстро обучается",
    "Хорошо ладит с другими животными", "Настоящий охранник", "Нежный и спокойный",
    "Немного стеснительный, но очень преданный", "Игривый и любознательный",
    "Умеет выполнять команды", "С отличным аппетитом", "Обожает внимание",
    "Требует немного терпения, но потом — лучший друг", "Любит сидеть на коленках",
    "Прекрасный компаньон для прогулок",
]

def create_pets(count: int) -> list[PetCreate]:
    pets = []

    for i in range(count):
        pet = PetCreate(
            name=random.choice(pet_names),
            breed=random.choice(pet_breeds),
            age=random.choice(list(range(1, 21))),
            color=random.choice(pet_colors),
            description=random.choice(pet_descriptions),
        )

        pets.append(pet)

    return pets


async def fill_db_pet(
        pet_data: PetCreate,
        session: AsyncSession,
) -> None:
    users = await UserServices.get_all_users(session)
    owner_id = (random.choice(users)).id

    await PetServices.create_pet(
        owner_id,
        pet_data,
        session,
    )

async def main(count: int) -> None:
    pets = create_pets(count)

    tasks = []
    for pet in pets:
        async def task(u: PetCreate = pet) -> None:
            async with async_session_maker() as session:
                await fill_db_pet(u, session)
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


