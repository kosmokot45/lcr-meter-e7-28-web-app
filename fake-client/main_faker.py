import serial
import serial.tools.list_ports
import random
import time
from threading import Thread
import sys


class FakeLCRMeter:
    def __init__(self, port=None, baudrate=9600, timeout=1):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial = None
        self.running = False
        self.measurement_mode = "LCR"  # Can be L, C, R, Z, etc.
        self.frequency = 1000  # Hz
        self.voltage = 1.0  # V
        self.measurement_count = 0

    def start(self):
        """Start the fake LCR meter server"""
        if self.port is None:
            self.port = self.find_available_port()
            if self.port is None:
                print("No available COM ports found!")
                return False

        try:
            self.serial = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=self.timeout,
            )
            self.running = True
            print(f"Fake LCR Meter running on {self.port}")
            return True
        except serial.SerialException as e:
            print(f"Failed to open serial port: {e}")
            return False

    def find_available_port(self):
        """Find an available COM port"""
        ports = serial.tools.list_ports.comports()
        for port in ports:
            if not port.device.startswith("COM"):  # Skip non-COM ports on Linux
                continue
            try:
                # Try to open the port to check availability
                test_serial = serial.Serial(port.device)
                test_serial.close()
                return port.device
            except (serial.SerialException, OSError):
                continue
        return None

    def stop(self):
        """Stop the fake LCR meter server"""
        self.running = False
        if self.serial and self.serial.is_open:
            self.serial.close()
        print("Fake LCR Meter stopped")

    def run(self):
        """Main server loop"""
        if not self.serial or not self.serial.is_open:
            return

        while self.running:
            if self.serial.in_waiting > 0:
                command = self.serial.readline().decode("ascii", errors="ignore").strip()
                self.process_command(command)

            # Simulate periodic measurements even without commands
            time.sleep(0.1)

    def process_command(self, command):
        """Process incoming commands from the client"""
        if not command:
            return

        print(f"Received command: {command}")

        # Simple command processing - real E7-28 would have more complex protocol
        if command.upper() == "*IDN?":
            self.send_response("FAKE,E7-28,Simulator,1.0")
        elif command.upper() == "MEASURE?":
            self.send_measurement()
        elif command.upper().startswith("FREQ "):
            try:
                self.frequency = float(command[5:])
                self.send_response("OK")
            except ValueError:
                self.send_response("ERROR")
        elif command.upper().startswith("VOLT "):
            try:
                self.voltage = float(command[5:])
                self.send_response("OK")
            except ValueError:
                self.send_response("ERROR")
        elif command.upper().startswith("MODE "):
            mode = command[5:].upper()
            if mode in ["L", "C", "R", "Z", "LCR"]:
                self.measurement_mode = mode
                self.send_response("OK")
            else:
                self.send_response("ERROR")
        elif command.upper() == "RESET":
            self.reset_settings()
            self.send_response("OK")
        else:
            self.send_response("ERROR: Unknown command")

    def send_response(self, response):
        """Send a response to the client"""
        if self.serial and self.serial.is_open:
            self.serial.write(f"{response}\r\n".encode("ascii"))

    def send_measurement(self):
        """Generate and send a fake measurement"""
        self.measurement_count += 1

        # Generate some realistic-looking values with slight randomness
        if self.measurement_mode == "L":
            value = 100e-6 * (1 + 0.01 * random.random())  # ~100µH with 1% variation
            unit = "H"
        elif self.measurement_mode == "C":
            value = 100e-9 * (1 + 0.01 * random.random())  # ~100nF with 1% variation
            unit = "F"
        elif self.measurement_mode == "R":
            value = 100 * (1 + 0.01 * random.random())  # ~100Ω with 1% variation
            unit = "Ω"
        elif self.measurement_mode == "Z":
            value = 120 * (1 + 0.01 * random.random())  # ~120Ω with 1% variation
            unit = "Ω"
        else:  # LCR mode
            value = f"L={100e-6*(1+0.01*random.random()):.6f},C={100e-9*(1+0.01*random.random()):.6f},R={100*(1+0.01*random.random()):.2f}"
            unit = ""

        if self.measurement_mode != "LCR":
            response = f"{value:.6f} {unit},F={self.frequency}Hz,V={self.voltage}V,#{self.measurement_count}"
        else:
            response = f"{value},F={self.frequency}Hz,V={self.voltage}V,#{self.measurement_count}"

        self.send_response(response)

    def reset_settings(self):
        """Reset to default settings"""
        self.measurement_mode = "LCR"
        self.frequency = 1000
        self.voltage = 1.0
        self.measurement_count = 0


def main():
    if len(sys.argv) > 1:
        port = sys.argv[1]
    else:
        port = None

    meter = FakeLCRMeter(port=port)
    if not meter.start():
        return

    try:
        # Run the server in a separate thread
        server_thread = Thread(target=meter.run)
        server_thread.daemon = True
        server_thread.start()

        print("Fake LCR Meter simulator is running. Press Ctrl+C to stop.")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        meter.stop()


if __name__ == "__main__":
    main()
