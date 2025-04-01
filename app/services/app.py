# # app.py
# from flask import Flask, render_template, request, jsonify, send_file
# import serial
# import serial.tools.list_ports
# import struct
# import time
# import csv
# import io
# from threading import Lock
# from datetime import datetime
# import random

# app = Flask(__name__)

# # Global variables for meter connection and data
# serial_connection = None
# serial_lock = Lock()
# measurement_data = []
# data_lock = Lock()
# is_measuring = False

# # Measurement configuration
# current_config = {"frequency": 1000, "mode": "Z", "speed": "normal", "range": "auto"}


# def connect_to_meter(port, baudrate=9600):
#     """Establish serial connection to LCR meter"""
#     global serial_connection

#     ports = serial.tools.list_ports.comports()
#     print("Available COM ports:")
#     for p in ports:
#         print(f"- {p.device}")

#     try:
#         with serial_lock:
#             if serial_connection and serial_connection.is_open:
#                 serial_connection.close()
#             serial_connection = serial.Serial(
#                 port=port,
#                 baudrate=baudrate,
#                 bytesize=serial.EIGHTBITS,
#                 parity=serial.PARITY_NONE,
#                 stopbits=serial.STOPBITS_ONE,
#                 timeout=1,
#             )
#         return True, f"Connected to {port}"
#     except Exception as e:
#         return False, f"Connection failed: {str(e)}"


# def disconnect_meter():
#     """Close serial connection"""
#     global serial_connection
#     with serial_lock:
#         if serial_connection and serial_connection.is_open:
#             serial_connection.close()
#         serial_connection = None
#     return True, "Disconnected"


# def send_command(command, params=None):
#     """Send command to LCR meter"""
#     if not serial_connection or not serial_connection.is_open:
#         return None

#     try:
#         with serial_lock:
#             # Format command according to protocol
#             if command == 67:  # Set frequency
#                 freq_int = int(current_config["frequency"] * 100)
#                 cmd = bytes([0xAA, command]) + struct.pack(">I", freq_int)
#             elif command == 72:  # Get measurement
#                 cmd = bytes([0xAA, command, 0])
#             else:
#                 cmd = bytes([0xAA, command])

#             serial_connection.write(cmd)

#             # Read response
#             if command in [64, 65]:  # Device name/ID
#                 response = serial_connection.read(8)  # AA + cmd + 4 bytes
#                 return response[2:].decode("ascii") if len(response) == 6 else None
#             elif command == 72:  # Measurement data
#                 response = serial_connection.read(22)
#                 if len(response) == 22:
#                     return parse_measurement(response)
#             else:
#                 response = serial_connection.read(2)  # Just AA + cmd
#                 return True if len(response) == 2 and response[0] == 0xAA and response[1] == command else False
#     except Exception as e:
#         print(f"Command error: {str(e)}")
#         return None


# def parse_measurement(data):
#     """Parse measurement data according to protocol"""
#     if len(data) != 22:
#         return None

#     # Unpack binary data
#     flags = data[0]
#     mode = data[1]
#     speed = data[2]
#     range_ = data[3]
#     # Uout1, Ucub skipped (bytes 4-7)
#     freq = struct.unpack(">I", data[8:12])[0] / 100.0
#     z_mag = struct.unpack(">f", data[12:16])[0]
#     phase_rad = struct.unpack(">f", data[16:20])[0]
#     phase_deg = phase_rad * 57.2957795  # Convert to degrees

#     # Determine measurement mode
#     mode_names = {0: "L", 1: "C", 2: "R", 3: "Z", 4: "Y", 5: "Q", 6: "D", 7: "θ"}

#     # Create measurement dictionary
#     timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
#     measurement = {
#         "timestamp": timestamp,
#         "mode": mode_names.get(mode, "?"),
#         "frequency": freq,
#         "z_mag": z_mag,
#         "phase_rad": phase_rad,
#         "phase_deg": phase_deg,
#         "speed": ["fast", "normal", "average"][speed] if speed < 3 else "?",
#         "range": range_,
#         "flags": flags,
#     }

#     # Add derived values based on mode
#     if mode == 0:  # L
#         measurement["value"] = z_mag / (2 * 3.14159 * freq)
#         measurement["unit"] = "H"
#     elif mode == 1:  # C
#         measurement["value"] = 1 / (z_mag * 2 * 3.14159 * freq)
#         measurement["unit"] = "F"
#     elif mode == 2:  # R
#         measurement["value"] = z_mag
#         measurement["unit"] = "Ω"
#     elif mode == 3:  # Z
#         measurement["value"] = z_mag
#         measurement["unit"] = "Ω"
#     elif mode == 7:  # θ
#         measurement["value"] = phase_deg
#         measurement["unit"] = "°"

#     return measurement


# def get_available_ports():
#     """Get list of available serial ports"""
#     ports = serial.tools.list_ports.comports()
#     return [port.device for port in ports]


# @app.route("/")
# def index():
#     """Main page with controls and visualizations"""
#     ports = get_available_ports()
#     return render_template("index.html", ports=ports)


# @app.route("/connect", methods=["POST"])
# def connect():
#     """Handle connection request"""
#     port = request.form.get("port")
#     if not port:
#         return jsonify({"success": False, "message": "No port selected"})

#     success, message = connect_to_meter(port)
#     if success:
#         # Get device info
#         device_name = send_command(64)
#         device_id = send_command(65)
#         return jsonify(
#             {
#                 "success": True,
#                 "message": message,
#                 "device": f"{device_name} ({device_id})" if device_name and device_id else "Unknown device",
#             }
#         )
#     else:
#         return jsonify({"success": False, "message": message})


# @app.route("/disconnect", methods=["POST"])
# def disconnect():
#     """Handle disconnection request"""
#     success, message = disconnect_meter()
#     return jsonify({"success": success, "message": message})


# @app.route("/get_config", methods=["GET"])
# def get_config():
#     """Get current configuration"""
#     return jsonify(current_config)


# @app.route("/set_config", methods=["POST"])
# def set_config():
#     """Update measurement configuration"""
#     global current_config
#     current_config.update(
#         {
#             "frequency": int(request.form.get("frequency", 1000)),
#             "mode": request.form.get("mode", "Z"),
#             "speed": request.form.get("speed", "normal"),
#             "range": request.form.get("range", "auto"),
#         }
#     )

#     # Send frequency command to meter
#     if serial_connection and serial_connection.is_open:
#         send_command(67)  # Set frequency

#     return jsonify({"success": True, "message": "Configuration updated"})


# @app.route("/start_measure", methods=["POST"])
# def start_measure():
#     """Start continuous measurement"""
#     global is_measuring
#     is_measuring = True

#     # Reset data
#     with data_lock:
#         measurement_data.clear()

#     return jsonify({"success": True, "message": "Measurement started"})


# @app.route("/stop_measure", methods=["POST"])
# def stop_measure():
#     """Stop continuous measurement"""
#     global is_measuring
#     is_measuring = False
#     return jsonify({"success": True, "message": "Measurement stopped"})


# @app.route("/get_measurements", methods=["GET"])
# def get_measurements():
#     """Get current measurement data"""
#     with data_lock:
#         # Take only the last 100 measurements for performance
#         recent_data = measurement_data[-100:]
#         return jsonify(recent_data)


# @app.route("/export_csv", methods=["GET"])
# def export_csv():
#     """Export measurement data as CSV"""
#     with data_lock:
#         if not measurement_data:
#             return jsonify({"success": False, "message": "No data to export"})

#         # Create CSV in memory
#         output = io.StringIO()
#         writer = csv.writer(output)

#         # Write header
#         writer.writerow(
#             ["Timestamp", "Mode", "Frequency (Hz)", "Value", "Unit", "|Z| (Ω)", "Phase (°)", "Speed", "Range"]
#         )

#         # Write data
#         for m in measurement_data:
#             writer.writerow(
#                 [
#                     m["timestamp"],
#                     m["mode"],
#                     m["frequency"],
#                     m.get("value", ""),
#                     m.get("unit", ""),
#                     m["z_mag"],
#                     m["phase_deg"],
#                     m["speed"],
#                     m["range"],
#                 ]
#             )

#         # Prepare response
#         output.seek(0)
#         timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
#         return send_file(
#             io.BytesIO(output.getvalue().encode("utf-8")),
#             mimetype="text/csv",
#             as_attachment=True,
#             download_name=f"lcr_measurements_{timestamp}.csv",
#         )


# def measurement_worker():
#     """Background worker for continuous measurements"""
#     global is_measuring, measurement_data

#     while True:
#         if is_measuring and serial_connection and serial_connection.is_open:
#             measurement = send_command(72)
#             if measurement:
#                 with data_lock:
#                     measurement_data.append(measurement)
#             time.sleep(0.1)  # Adjust based on desired measurement rate
#         else:
#             time.sleep(0.5)


# if __name__ == "__main__":
#     # Start measurement thread
#     import threading

#     thread = threading.Thread(target=measurement_worker)
#     thread.daemon = True
#     thread.start()

#     # Start Flask app
#     app.run(debug=True, threaded=True)
