from pydantic import TypeAdapter

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware

from src.config.logger import setup_logging
from src.schemas.pet import Pet
from src.schemas.report import Report
from src.schemas.user import User

TypeAdapter(User).rebuild()
TypeAdapter(Pet).rebuild()
TypeAdapter(Report).rebuild()

# API routers
from src.fastapi.routers.api.users import router as users_api_router
from src.fastapi.routers.api.pets import router as pets_api_router
from src.fastapi.routers.api.reports import router as reports_api_router

# VIEWS routers
from src.fastapi.routers.views.menu import router as menu_router
from src.fastapi.routers.views.other import router as other_router
from src.fastapi.routers.views.auth import router as auth_router
from src.fastapi.routers.views.register import router as register_router

setup_logging()
app = FastAPI(title="DogAlert")

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

# API routers
app.include_router(users_api_router)
app.include_router(pets_api_router)
app.include_router(reports_api_router)

# VIEWS routers
app.include_router(menu_router)
app.include_router(other_router)
app.include_router(auth_router)
app.include_router(register_router)


app.mount("/static", StaticFiles(directory="src/fastapi/static"), name="static")
templates = Jinja2Templates(directory="src/fastapi/templates")
