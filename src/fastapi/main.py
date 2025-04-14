from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from src.fastapi.routers.users import router as users_router

app = FastAPI()
app.include_router(users_router)

templates = Jinja2Templates(directory="src/fastapi/templates")

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")
