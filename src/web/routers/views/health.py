import asyncio
import logging
from datetime import datetime

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.datastructures import UploadFile

from src.database.db_session import get_async_session
from src.schemas.pet import PetUpdate
from src.services.pet_service import PetServices
from src.services.user_service import UserServices
from src.web.dependencies.date_format import format_russian_date
from src.web.dependencies.date_parsing import parse_date
from src.web.dependencies.get_data_from_cookie import get_user_id_from_cookie

log = logging.getLogger(__name__)

templates = Jinja2Templates(directory="src/web/templates")

router = APIRouter(
    prefix="/health",
    tags=["Health"],
)

@router.get("/edit_page/{pet_id}", response_class=HTMLResponse, include_in_schema=True)
async def show_edit_health_page(
        request: Request,
        pet_id: int,
        session: AsyncSession = Depends(get_async_session),
) -> HTMLResponse:
    user_id_str = get_user_id_from_cookie(request)

    if not user_id_str:
        return templates.TemplateResponse("no_telegram_login.html", {"request": request})

    user_id = int(user_id_str)

    from sqlalchemy import select

    await session.execute(select(1))

    async with asyncio.TaskGroup() as tg:
        user_db_task = tg.create_task(UserServices.find_one_or_none_by_user_id(user_id, session))
        user_pets_tasks = tg.create_task(UserServices.get_all_user_pets(user_id, session))
        pet_task = tg.create_task(PetServices.find_one_or_none_by_id(pet_id, session))

    user_db = user_db_task.result()
    user_pets = user_pets_tasks.result()
    pet = pet_task.result()

    if user_db is None or user_pets is None:
        return templates.TemplateResponse("no_telegram_login.html", {"request": request})

    user_pets_ids = [pet.id for pet in user_pets if pet is not None]

    if pet is None or pet.id not in user_pets_ids:
        return templates.TemplateResponse("something_goes_wrong.html", {"request": request})

    def format_date_for_none(date: datetime | None) -> str | None:
        return date.strftime("%Y-%m-%d") if date else None

    if pet:
        formatted_pet = {
            "id": pet.id,
            "name": pet.name,
            "breed": pet.breed,
            "age": pet.age,
            "color": pet.color,
            "description": pet.description,
            "last_vaccination": format_russian_date(pet.last_vaccination),
            "next_vaccination": format_russian_date(pet.next_vaccination),
            "last_parasite_treatment": format_russian_date(pet.last_parasite_treatment),
            "next_parasite_treatment": format_russian_date(pet.next_parasite_treatment),
            "last_fleas_ticks_treatment": format_russian_date(pet.last_fleas_ticks_treatment),
            "next_fleas_ticks_treatment": format_russian_date(pet.next_fleas_ticks_treatment),
            # ISO format for Form fields
            "last_vaccination_iso": format_date_for_none(pet.last_vaccination),
            "next_vaccination_iso": format_date_for_none(pet.next_vaccination),
            "last_parasite_treatment_iso": format_date_for_none(pet.last_parasite_treatment),
            "next_parasite_treatment_iso": format_date_for_none(pet.next_parasite_treatment),
            "last_fleas_ticks_treatment_iso": format_date_for_none(pet.last_fleas_ticks_treatment),
            "next_fleas_ticks_treatment_iso": format_date_for_none(pet.next_fleas_ticks_treatment),
        }
    return templates.TemplateResponse("pet/edit_health.html", {
        "request": request,
        "pet": formatted_pet,
        "pet_id": pet_id,
    })

@router.patch("/update_pet_health/{pet_id}", response_model=None, include_in_schema=True)
async def update_pet_health(
    request: Request,
    pet_id: int,
    session: AsyncSession = Depends(get_async_session),
) -> JSONResponse:
    user_id_str = get_user_id_from_cookie(request)
    if not user_id_str:
        return JSONResponse(
            content={
                "status": "error",
                "message": "Пользователь не найден",
            },
            status_code=404,
        )

    user_id = int(user_id_str)

    try:
        form_data = await request.form()
        log.info(f"Received form data: {dict(form_data)}")
    except Exception as e:
        return JSONResponse(
            content={"status": "error", "message": f"Ошибка чтения формы: {str(e)}"},
            status_code=400,
        )

    async with asyncio.TaskGroup() as tg:
        user_task = tg.create_task(UserServices.find_one_or_none_by_user_id(user_id, session))
        pet_task = tg.create_task(PetServices.find_one_or_none_by_id(pet_id, session))

    user = user_task.result()
    pet = pet_task.result()

    if user is None:
        return JSONResponse(
            content={"status": "error", "message": "Пользователь не найден"},
            status_code=400,
        )
    if pet is None:
        return JSONResponse(
            content={"status": "error", "message": "Питомец не найден"},
            status_code=400,
        )

    pet_owners_ids = [owner.id for owner in pet.owners]
    if user.id not in pet_owners_ids:
        return JSONResponse(
            content={"status": "error", "message": "Вы не являетесь владельцем питомца"},
            status_code=400,
        )
    def check_form_data_str(data: UploadFile | str | None) -> str | None:
        if isinstance(data, str) and data.strip():
            return data.strip()
        return None

    last_vaccination_str = check_form_data_str(
        form_data.get("last_vaccination"),
    )
    next_vaccination_str = check_form_data_str(
        form_data.get("next_vaccination"),
    )
    last_parasite_treatment_str = check_form_data_str(
        form_data.get("last_parasite_treatment"),
    )
    next_parasite_treatment_str = check_form_data_str(
        form_data.get("next_parasite_treatment"),
    )
    last_fleas_ticks_treatment_str = check_form_data_str(
        form_data.get("last_fleas_ticks_treatment"),
    )
    next_fleas_ticks_treatment_str = check_form_data_str(
        form_data.get("next_fleas_ticks_treatment"),
    )

    parsed_last_vaccination = parse_date(last_vaccination_str, pet.last_vaccination)
    parsed_next_vaccination = parse_date(next_vaccination_str, pet.next_vaccination)
    parsed_last_parasite_treatment = parse_date(
        last_parasite_treatment_str,
        pet.last_parasite_treatment,
    )
    parsed_next_parasite_treatment = parse_date(
        next_parasite_treatment_str,
        pet.next_parasite_treatment,
    )
    parsed_last_fleas_ticks_treatment = parse_date(
        last_fleas_ticks_treatment_str,
        pet.last_fleas_ticks_treatment,
    )
    parsed_next_fleas_ticks_treatment = parse_date(
        next_fleas_ticks_treatment_str,
        pet.next_fleas_ticks_treatment,
    )

    update_data: dict[str, datetime | None] = {}
    if last_vaccination_str is not None:
        update_data["last_vaccination"] = parsed_last_vaccination
    if next_vaccination_str is not None:
        update_data["next_vaccination"] = parsed_next_vaccination
    if last_parasite_treatment_str is not None:
        update_data["last_parasite_treatment"] = parsed_last_parasite_treatment
    if next_parasite_treatment_str is not None:
        update_data["next_parasite_treatment"] = parsed_next_parasite_treatment
    if last_fleas_ticks_treatment_str is not None:
        update_data["last_fleas_ticks_treatment"] = parsed_last_fleas_ticks_treatment
    if next_fleas_ticks_treatment_str is not None:
        update_data["next_fleas_ticks_treatment"] = parsed_next_fleas_ticks_treatment

    log.info(f"Update data: {update_data}")
    if update_data:
        try:
            pet_update_schema = PetUpdate(**update_data)  # type: ignore[arg-type]
            log.info(f"Created PetUpdate schema: {pet_update_schema}")
            pet_updated = await PetServices.update_pet(
                pet_id=pet_id,
                pet_data=pet_update_schema,
                session=session,
            )
            log.info(f"Pet updated successfully: {pet_updated}")
        except Exception as e:
            return JSONResponse(
                content={"status": "error", "message": f"Ошибка при обновлении {e}"},
                status_code=500,
            )
    else:
        log.info("No data to update")

    return JSONResponse(
        content={
            "status": "success",
            "message": "Данные о здоровье питомца обновлены.",
            "redirect_url": "/health/",
        },
    )
