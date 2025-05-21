from src.database.models import Report as Report_db
from src.database.models import Pet as Pet_db


def notification_content(report_created: Report_db, report_pet: Pet_db) -> str:
    return (f"❗❗❗ ОБЪЯВЛЕНИЕ О ПРОПАЖЕ ❗❗❗\n\n"
            f"{report_created.title}\n"
            f"{report_created.content}\n\n"
            f"Информация о пропавшем питомце:\n"
            f"Кличка: {report_pet.name}\n"
            f"Порода: {report_pet.breed}\n"
            f"Возраст: {report_pet.age}\n"
            f"Цвет: {report_pet.color}\n"
            f"Особенности: {report_pet.description}"
            )
