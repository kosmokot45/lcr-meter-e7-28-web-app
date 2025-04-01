from threading import Lock
from datetime import datetime
import time
import csv
import io
from typing import List, Dict, Any

from app.services.meter import send_command
from app.models.schemas import MeasurementData

# Global variables for measurement data
measurement_data: List[Dict[str, Any]] = []
data_lock = Lock()
is_measuring = bool = False
current_config: Dict[str, Any] = {"frequency": 1000, "mode": "Z", "speed": "normal", "range": "auto"}


def get_measurements(limit: int = 100) -> List[Dict[str, Any]]:
    """Get recent measurement data"""
    with data_lock:
        return measurement_data[-limit:]


def clear_measurements() -> None:
    """Clear measurement data"""
    with data_lock:
        measurement_data.clear()


def start_measurement() -> None:
    """Start continuous measurement"""
    global is_measuring
    is_measuring = True


def stop_measurement() -> None:
    """Stop continuous measurement"""
    global is_measuring
    is_measuring = False


def update_config(new_config: Dict[str, Any]) -> None:
    """Update measurement configuration"""
    global current_config
    current_config.update(new_config)
    # Send frequency command to meter
    send_command(67, current_config)  # Set frequency


def get_config() -> Dict[str, Any]:
    """Get current configuration"""
    return current_config


def export_to_csv() -> io.BytesIO:
    """Export measurement data as CSV"""
    with data_lock:
        if not measurement_data:
            return None

        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow(
            ["Timestamp", "Mode", "Frequency (Hz)", "Value", "Unit", "|Z| (Ω)", "Phase (°)", "Speed", "Range"]
        )

        # Write data
        for m in measurement_data:
            writer.writerow(
                [
                    m["timestamp"],
                    m["mode"],
                    m["frequency"],
                    m.get("value", ""),
                    m.get("unit", ""),
                    m["z_mag"],
                    m["phase_deg"],
                    m["speed"],
                    m["range"],
                ]
            )

        # Prepare response
        output.seek(0)
        csv_bytes = io.BytesIO(output.getvalue().encode("utf-8"))
        csv_bytes.seek(0)
        return csv_bytes


def measurement_worker() -> None:
    """Background worker for continuous measurements"""
    global is_measuring, measurement_data, current_config

    while True:
        if is_measuring:
            measurement = send_command(72)
            if measurement:
                with data_lock:
                    measurement_data.append(measurement)
            time.sleep(0.1)  # Adjust based on desired measurement rate
        else:
            time.sleep(0.5)
