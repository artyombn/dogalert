from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import aiohttp
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import TypeAdapter

from src.config.logger import setup_logging
from src.schemas.pet import Pet
from src.schemas.report import Report
from src.schemas.user import User
from src.web.routers.api.geo import router as geo_api_router
from src.web.routers.api.notifications import router as notifications_api_router

# API routers
from src.web.routers.api.pets import router as pets_api_router
from src.web.routers.api.reports import router as reports_api_router
from src.web.routers.api.users import router as users_api_router

# VIEWS routers
from src.web.routers.views.auth import router as auth_router
from src.web.routers.views.geo import router as geo_router
from src.web.routers.views.menu import router as menu_router
from src.web.routers.views.other import router as other_router
from src.web.routers.views.pet_router import router as pet_router
from src.web.routers.views.register import router as register_router
from src.web.routers.views.report_router import router as new_report_router
from src.web.routers.views.user_router import router as user_router

TypeAdapter(User).rebuild()
TypeAdapter(Pet).rebuild()
TypeAdapter(Report).rebuild()

setup_logging()

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    connector = aiohttp.TCPConnector(limit=5)  # !!! ssl=False НЕ ДЛЯ ПРОДА
    session = aiohttp.ClientSession(connector=connector)
    app.state.aiohttp_session = session
    yield
    await session.close()

app = FastAPI(
    title="DogAlert",
    lifespan=lifespan,
    docs_url=None,
    redoc_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routers
app.include_router(users_api_router)
app.include_router(pets_api_router)
app.include_router(reports_api_router)
app.include_router(geo_api_router)
app.include_router(notifications_api_router)

# VIEWS routers
app.include_router(menu_router)
app.include_router(other_router)
app.include_router(auth_router)
app.include_router(register_router)
app.include_router(new_report_router)
app.include_router(pet_router)
app.include_router(user_router)
app.include_router(geo_router)


app.mount("/static", StaticFiles(directory="src/web/static"), name="static")
templates = Jinja2Templates(directory="src/web/templates")

