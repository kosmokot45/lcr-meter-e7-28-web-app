from pydantic import BaseModel
from typing import Optional, List


class MeasurementConfig(BaseModel):
    frequency: int = 1000
    mode: str = "Z"
    speed: str = "normal"
    range: str = "auto"


class MeasurementData(BaseModel):
    timestamp: str
    mode: str
    frequency: float
    z_mag: float
    phase_rad: float
    phase_deg: float
    speed: str
    range: int
    flags: int
    value: Optional[float] = None
    unit: Optional[str] = None


class ConnectionRequest(BaseModel):
    port: str


class DeviceInfo(BaseModel):
    success: bool
    message: str
    device: Optional[str] = None
