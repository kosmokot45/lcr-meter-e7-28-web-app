import serial
import serial.tools.list_ports
import struct
from threading import Lock
from typing import Tuple, Optional, Dict, Any

serial_connection = None
serial_lock = Lock()


def get_available_ports() -> list:
    """Get list of available serial ports"""
    ports = serial.tools.list_ports.comports()
    return [port.device for port in ports]


def connect_to_meter(port: str, baudrate: int = 9600) -> Tuple[bool, str]:
    """Establish serial connection to LCR meter"""
    global serial_connection

    try:
        with serial_lock:
            if serial_connection and serial_connection.is_open:
                serial_connection.close()
            serial_connection = serial.Serial(
                port=port,
                baudrate=baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=1,
            )
        return True, f"Connected to {port}"
    except Exception as e:
        return False, f"Connection failed: {str(e)}"


def disconnect_meter() -> Tuple[bool, str]:
    """Close serial connection"""
    global serial_connection
    with serial_lock:
        if serial_connection and serial_connection.is_open:
            serial_connection.close()
        serial_connection = None
    return True, "Disconnected"


def send_command(command: int, config: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
    """Send command to LCR meter"""
    if not serial_connection or not serial_connection.is_open:
        return None

    try:
        with serial_lock:
            # Format command according to protocol
            if command == 67:  # Set frequency
                freq_int = int(config["frequency"] * 100) if config else 100000
                cmd = bytes([0xAA, command]) + struct.pack(">I", freq_int)
            elif command == 72:  # Get measurement
                cmd = bytes([0xAA, command, 0])
            else:
                cmd = bytes([0xAA, command])

            serial_connection.write(cmd)

            # Read response
            if command in [64, 65]:  # Device name/ID
                response = serial_connection.read(8)  # AA + cmd + 4 bytes
                return response[2:].decode("ascii") if len(response) == 6 else None
            elif command == 72:  # Measurement data
                response = serial_connection.read(22)
                if len(response) == 22:
                    return parse_measurement(response)
            else:
                response = serial_connection.read(2)  # Just AA + cmd
                return True if len(response) == 2 and response[0] == 0xAA and response[1] == command else False
    except Exception as e:
        print(f"Command error: {str(e)}")
        return None


def parse_measurement(data: bytes) -> Dict[str, Any]:
    """Parse measurement data according to protocol"""
    if len(data) != 22:
        return None

    # Unpack binary data
    flags = data[0]
    mode = data[1]
    speed = data[2]
    range_ = data[3]
    freq = struct.unpack(">I", data[8:12])[0] / 100.0
    z_mag = struct.unpack(">f", data[12:16])[0]
    phase_rad = struct.unpack(">f", data[16:20])[0]
    phase_deg = phase_rad * 57.2957795  # Convert to degrees

    # Determine measurement mode
    mode_names = {0: "L", 1: "C", 2: "R", 3: "Z", 4: "Y", 5: "Q", 6: "D", 7: "θ"}

    # Create measurement dictionary
    from datetime import datetime

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    measurement = {
        "timestamp": timestamp,
        "mode": mode_names.get(mode, "?"),
        "frequency": freq,
        "z_mag": z_mag,
        "phase_rad": phase_rad,
        "phase_deg": phase_deg,
        "speed": ["fast", "normal", "average"][speed] if speed < 3 else "?",
        "range": range_,
        "flags": flags,
    }

    # Add derived values based on mode
    if mode == 0:  # L
        measurement["value"] = z_mag / (2 * 3.14159 * freq)
        measurement["unit"] = "H"
    elif mode == 1:  # C
        measurement["value"] = 1 / (z_mag * 2 * 3.14159 * freq)
        measurement["unit"] = "F"
    elif mode == 2:  # R
        measurement["value"] = z_mag
        measurement["unit"] = "Ω"
    elif mode == 3:  # Z
        measurement["value"] = z_mag
        measurement["unit"] = "Ω"
    elif mode == 7:  # θ
        measurement["value"] = phase_deg
        measurement["unit"] = "°"

    return measurement
