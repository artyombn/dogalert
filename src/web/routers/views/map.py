import logging

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

logger = logging.getLogger(__name__)

templates = Jinja2Templates(directory="src/web/templates")
router = APIRouter(
    prefix="/map",
    tags=["Map"],
)

@router.get("/", response_class=HTMLResponse)
async def map_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("map/index.html", {"request": request})
