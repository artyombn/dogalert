import asyncio
import logging
from datetime import datetime

from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

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

    if user_db is None:
        return templates.TemplateResponse("no_telegram_login.html", {"request": request})

    user_pets_ids = [pet.id for pet in user_pets]

    if pet.id not in user_pets_ids:
        return templates.TemplateResponse("something_goes_wrong.html", {"request": request})

    if pet:
        formatted_pet = {
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
            "last_vaccination_iso": pet.last_vaccination.strftime('%Y-%m-%d') if pet.last_vaccination else None,
            "next_vaccination_iso": pet.next_vaccination.strftime('%Y-%m-%d') if pet.next_vaccination else None,
            "last_parasite_treatment_iso": pet.last_parasite_treatment.strftime('%Y-%m-%d') if pet.last_parasite_treatment else None,
            "next_parasite_treatment_iso": pet.next_parasite_treatment.strftime('%Y-%m-%d') if pet.next_parasite_treatment else None,
            "last_fleas_ticks_treatment_iso": pet.last_fleas_ticks_treatment.strftime('%Y-%m-%d') if pet.last_fleas_ticks_treatment else None,
            "next_fleas_ticks_treatment_iso": pet.next_fleas_ticks_treatment.strftime('%Y-%m-%d') if pet.next_fleas_ticks_treatment else None,
        }
    return templates.TemplateResponse("pet/edit_health.html", {
        "request": request,
        "pet": formatted_pet,
    })

@router.patch("/update_pet_health/{pet_id}", response_model=None, include_in_schema=True)
async def update_pet_health(
        request: Request,
        pet_id: int,
        last_vaccination: datetime | None = Form(None, example=None),
        next_vaccination: datetime | None = Form(None, example=None),
        last_parasite_treatment: datetime | None = Form(None, example=None),
        next_parasite_treatment: datetime | None = Form(None, example=None),
        last_fleas_ticks_treatment: datetime | None = Form(None, example=None),
        next_fleas_ticks_treatment: datetime | None = Form(None, example=None),
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
        print(f"Received form data: {dict(form_data)}")
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

    parsed_last_vaccination = parse_date(last_vaccination, pet.last_vaccination)
    parsed_next_vaccination = parse_date(next_vaccination, pet.next_vaccination)
    parsed_last_parasite_treatment = parse_date(last_parasite_treatment, pet.last_parasite_treatment)
    parsed_next_parasite_treatment = parse_date(next_parasite_treatment, pet.next_parasite_treatment)
    parsed_last_fleas_ticks_treatment = parse_date(last_fleas_ticks_treatment, pet.last_fleas_ticks_treatment)
    parsed_next_fleas_ticks_treatment = parse_date(next_fleas_ticks_treatment, pet.next_fleas_ticks_treatment)

    update_data: dict[str, datetime] = {}
    if last_vaccination is not None:
        update_data["last_vaccination"] = parsed_last_vaccination

    if next_vaccination is not None:
        update_data["next_vaccination"] = parsed_next_vaccination
        log.info(f"parsed_next_vaccination != pet.next_vaccination --> {parsed_next_vaccination != pet.next_vaccination}")
        log.info(f"parsed_next_vaccination = {parsed_next_vaccination}")
        log.info(f"pet.next_vaccination = {pet.next_vaccination}")
        if parsed_next_vaccination != pet.next_vaccination:
            if parsed_next_vaccination is not None:
                await PetServices.update_next_vaccination_dates(pet.id, parsed_next_vaccination, session)
            else:
                await PetServices.cancel_vaccination_reminder(pet.id, session)

    if last_parasite_treatment is not None:
        update_data["last_parasite_treatment"] = parsed_last_parasite_treatment

    if next_parasite_treatment is not None:
        update_data["next_parasite_treatment"] = parsed_next_parasite_treatment
        log.info(f"parsed_next_parasite_treatment != pet.next_parasite_treatment --> {parsed_next_parasite_treatment != pet.next_parasite_treatment}")
        if parsed_next_parasite_treatment != pet.next_parasite_treatment:
            if parsed_next_parasite_treatment is not None:
                await PetServices.update_next_parasite_dates(pet.id, parsed_next_parasite_treatment, session)
            else:
                await PetServices.cancel_parasite_reminder(pet.id, session)

    if last_fleas_ticks_treatment is not None:
        update_data["last_fleas_ticks_treatment"] = parsed_last_fleas_ticks_treatment

    if next_fleas_ticks_treatment is not None:
        update_data["next_fleas_ticks_treatment"] = parsed_next_fleas_ticks_treatment
        log.info(f"parsed_next_fleas_ticks_treatment != pet.next_fleas_ticks_treatment --> {parsed_next_fleas_ticks_treatment != pet.next_fleas_ticks_treatment}")
        if parsed_next_fleas_ticks_treatment != pet.next_fleas_ticks_treatment:
            if parsed_next_fleas_ticks_treatment is not None:
                await PetServices.update_next_fleas_ticks_dates(pet.id, parsed_next_fleas_ticks_treatment, session)
            else:
                await PetServices.cancel_fleas_ticks_reminder(pet.id, session)

    log.info(f"Update data: {update_data}")
    if update_data:
        try:
            pet_update_schema = PetUpdate(**update_data)
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

    return JSONResponse(
        content={
            "status": "success",
            "message": "Данные о здоровье питомца обновлены.\nУведомления также были обновлены.",
            "redirect_url": f"/health/",
        }
    )

