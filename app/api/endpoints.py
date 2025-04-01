# from fastapi import APIRouter, Request, HTTPException
# from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
# from fastapi.templating import Jinja2Templates
# from typing import List

# from app.services.meter import get_available_ports, connect_to_meter, disconnect_meter, send_command
# from app.services.measurement import (
#     get_measurements,
#     start_measurement,
#     stop_measurement,
#     update_config,
#     get_config,
#     export_to_csv,
#     clear_measurements,
# )
# from app.models.schemas import MeasurementConfig, ConnectionRequest, DeviceInfo, MeasurementData

# router = APIRouter()
# templates = Jinja2Templates(directory="app/templates")


# @router.get("/", response_class=HTMLResponse)
# async def index(request: Request):
#     """Main page with controls and visualizations"""
#     ports = get_available_ports()
#     return templates.TemplateResponse("index.html", {"request": request, "ports": ports})


# @router.post("/connect", response_model=DeviceInfo)
# async def connect(request: ConnectionRequest):
#     """Handle connection request"""
#     if not request.port:
#         raise HTTPException(status_code=400, detail="No port selected")

#     success, message = connect_to_meter(request.port)
#     if success:
#         # Get device info
#         device_name = send_command(64)
#         device_id = send_command(65)
#         return {
#             "success": True,
#             "message": message,
#             "device": f"{device_name} ({device_id})" if device_name and device_id else "Unknown device",
#         }
#     else:
#         return {"success": False, "message": message}


# @router.post("/disconnect")
# async def disconnect():
#     """Handle disconnection request"""
#     success, message = disconnect_meter()
#     return {"success": success, "message": message}


# @router.get("/config", response_model=MeasurementConfig)
# async def get_current_config():
#     """Get current configuration"""
#     return get_config()


# @router.post("/config")
# async def set_config(config: MeasurementConfig):
#     """Update measurement configuration"""
#     update_config(config.dict())
#     return {"success": True, "message": "Configuration updated"}


# @router.post("/measure/start")
# async def start_measure():
#     """Start continuous measurement"""
#     clear_measurements()
#     start_measurement()
#     return {"success": True, "message": "Measurement started"}


# @router.post("/measure/stop")
# async def stop_measure():
#     """Stop continuous measurement"""
#     stop_measurement()
#     return {"success": True, "message": "Measurement stopped"}


# @router.get("/measure/data", response_model=List[MeasurementData])
# async def get_measurement_data():
#     """Get current measurement data"""
#     return get_measurements()


# @router.get("/measure/export")
# async def export_measurements():
#     """Export measurement data as CSV"""
#     csv_file = export_to_csv()
#     if not csv_file:
#         raise HTTPException(status_code=400, detail="No data to export")

#     from datetime import datetime

#     timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
#     return FileResponse(csv_file, media_type="text/csv", filename=f"lcr_measurements_{timestamp}.csv")
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, FileResponse
import csv
import io
from datetime import datetime

from app.services.measurement import (
    get_measurements,
    start_measurement,
    stop_measurement,
    update_config,
    get_config,
    export_to_csv,
)
from app.services.meter import connect_to_meter, disconnect_meter, send_command

router = APIRouter()


@router.post("/connect")
async def connect(request: Request):
    data = await request.json()
    port = data.get("port")
    if not port:
        return JSONResponse({"success": False, "message": "No port selected"})

    success, message = connect_to_meter(port)
    if success:
        device_name = send_command(64)
        device_id = send_command(65)
        return JSONResponse(
            {
                "success": True,
                "message": message,
                "device": f"{device_name} ({device_id})" if device_name and device_id else "Unknown device",
            }
        )
    return JSONResponse({"success": False, "message": message})


@router.post("/disconnect")
async def disconnect():
    success, message = disconnect_meter()
    return JSONResponse({"success": success, "message": message})


@router.get("/get_config")
async def get_current_config():
    return JSONResponse(get_config())


@router.post("/set_config")
async def set_config(request: Request):
    config = await request.json()
    update_config(config)
    return JSONResponse({"success": True, "message": "Configuration updated"})


@router.post("/start_measure")
async def start_measure():
    start_measurement()
    return JSONResponse({"success": True, "message": "Measurement started"})


@router.post("/stop_measure")
async def stop_measure():
    stop_measurement()
    return JSONResponse({"success": True, "message": "Measurement stopped"})


@router.get("/get_measurements")
async def get_measurement_data():
    measurements = get_measurements()
    return JSONResponse(measurements)


@router.get("/export_csv")
async def export_measurements():
    csv_file = export_to_csv()
    if not csv_file:
        return JSONResponse({"success": False, "message": "No data to export"})

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return FileResponse(csv_file, media_type="text/csv", filename=f"lcr_measurements_{timestamp}.csv")
