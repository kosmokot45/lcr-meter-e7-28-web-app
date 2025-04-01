# from pathlib import Path

# from fastapi import APIRouter, Request
# from fastapi import HTTPException
# from fastapi import status
# from fastapi import Depends
# from sqlalchemy.ext.asyncio import AsyncSession

# from fastapi.responses import HTMLResponse

# from fastapi.templating import Jinja2Templates


# router = APIRouter(prefix="/router")

# BASE_DIR = Path(__file__).resolve().parent

# # router.mount("/src/static", StaticFiles(directory="src/static"), name="static")

# templates = Jinja2Templates(directory=str(Path(BASE_DIR, "templates")))


# @router.get("/", response_class=HTMLResponse)
# async def home(request: Request):
#     # return templates.TemplateResponse(request=request, name="index.html")
#     return templates.TemplateResponse("index.html", {"request": request})
