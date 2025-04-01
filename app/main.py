# from fastapi import FastAPI, Request
# from fastapi.staticfiles import StaticFiles
# from fastapi.templating import Jinja2Templates
# from fastapi.responses import HTMLResponse
# import os

# app = FastAPI()

# # Configure paths
# base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# static_dir = os.path.join(base_dir, "app", "static")
# templates_dir = os.path.join(base_dir, "app", "templates")

# # Mount static files
# app.mount("/static", StaticFiles(directory=static_dir), name="static")

# # Setup templates
# templates = Jinja2Templates(directory=templates_dir)

# # Include API routes
# from app.api.endpoints import router as api_router
# app.include_router(api_router, prefix="/api")

# @app.get("/", response_class=HTMLResponse)
# async def home(request: Request):
#     """Serve the main interface page"""
#     # Get available ports for the dropdown
#     from app.services.meter import get_available_ports
#     ports = get_available_ports()
#     return templates.TemplateResponse("index.html", {"request": request, "ports": ports})
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import os

app = FastAPI()

# Configure paths
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
static_dir = os.path.join(base_dir, "app", "static")
templates_dir = os.path.join(base_dir, "app", "templates")

# Mount static files
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Setup templates
templates = Jinja2Templates(directory=templates_dir)

# Include API routes
from app.api.endpoints import router as api_router

app.include_router(api_router, prefix="/api")


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Serve the main interface page"""
    # Get available ports for the dropdown
    from app.services.meter import get_available_ports

    ports = get_available_ports()
    return templates.TemplateResponse("index.html", {"request": request, "ports": ports})
