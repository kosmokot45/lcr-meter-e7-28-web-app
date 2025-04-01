import serial
import serial.tools.list_ports
import random
import time
import struct
from threading import Thread
import sys
from enum import IntEnum


class MeasurementMode(IntEnum):
    L = 0
    C = 1
    R = 2
    Z = 3
    Y = 4
    Q = 5
    D = 6
    THETA = 7


class SpeedMode(IntEnum):
    FAST = 0
    NORMAL = 1
    AVERAGE_10 = 2


class RangeMode(IntEnum):
    AUTO = 0
    R10M = 1
    R1M = 2
    R100K = 3
    R10K = 4
    R1K = 5
    R100 = 6
    R10 = 7


class FakeLCRMeter:
    def __init__(self, port=None, baudrate=9600, timeout=1):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial = None
        self.running = False

        # Device state
        self.frequency = 1000  # Hz
        self.voltage = 1.0  # V
        self.mode = MeasurementMode.Z
        self.speed = SpeedMode.NORMAL
        self.range = RangeMode.AUTO
        self.compensation = False
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
            print(f"Fake LCR Meter E7-28 running on {self.port}")
            print("Simulating the binary protocol as described in the manual")
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
                # Read the command header (0xAA + command byte)
                header = self.serial.read(2)
                if len(header) != 2:
                    continue

                if header[0] != 0xAA:
                    print(f"Invalid command header: {header[0]:02X}")
                    continue

                command = header[1]
                self.process_command(command)

            # Small delay to prevent CPU overuse
            time.sleep(0.01)

    def process_command(self, command):
        """Process incoming commands according to the protocol"""
        try:
            if command == 64:  # Get device name
                self.send_response(64, b"E728")

            elif command == 65:  # Get device ID (same as name in this case)
                self.send_response(65, b"E728")

            elif command == 66:  # Disable AVP (Auto Voltage Protection)
                self.send_response(66)

            elif command == 67:  # Set frequency
                # Read 4 bytes (big-endian uint32, frequency * 100)
                freq_bytes = self.serial.read(4)
                if len(freq_bytes) == 4:
                    freq_int = struct.unpack(">I", freq_bytes)[0]
                    self.frequency = freq_int / 10.0
                    self.send_response(67)
                    print("Success")
                else:
                    print("Invalid frequency command - missing bytes")

            elif command == 70:  # Set offset
                # Read 2 bytes (int16, offset * 10)
                offset_bytes = self.serial.read(2)
                if len(offset_bytes) == 2:
                    offset = struct.unpack(">h", offset_bytes)[0] / 10.0
                    self.send_response(70)
                else:
                    print("Invalid offset command - missing bytes")

            elif command == 71:  # Reset to defaults
                self.frequency = 1000
                self.voltage = 1.0
                self.mode = MeasurementMode.Z
                self.speed = SpeedMode.NORMAL
                self.range = RangeMode.AUTO
                self.compensation = False
                self.send_response(71)

            elif command == 72:  # Get full measurement data
                # Check if we need to read a parameter byte
                param = self.serial.read(1)
                if param and param[0] == 0:
                    # Measurement not ready response
                    self.send_response(72, bytes([0]))
                else:
                    # Generate fake measurement data
                    self.measurement_count += 1

                    # Flags byte (bitmask)
                    flags = 0
                    if self.compensation:
                        flags |= 0x01  # AVP bit
                    flags |= 0x80  # Measurement complete bit

                    # Generate fake impedance values
                    z_mag = 100.0 * (1 + 0.01 * random.random())  # ~100Ω with 1% variation
                    phase_rad = random.uniform(-0.5, 0.5)  # Random phase angle in radians

                    # Pack the data according to protocol
                    data = bytes(
                        [
                            flags,
                            self.mode,
                            self.speed,
                            self.range,
                            0,
                            0,  # Uout1 (placeholder)
                            0,
                            0,  # Ucub (placeholder)
                        ]
                    )

                    # Add frequency (4 bytes, big-endian uint32, frequency * 100)
                    freq_int = int(self.frequency * 100)
                    data += struct.pack(">I", freq_int)

                    # Add impedance magnitude (4 bytes float)
                    data += struct.pack(">f", z_mag)

                    # Add phase angle (4 bytes float, in radians)
                    data += struct.pack(">f", phase_rad)

                    self.send_response(72, data)

            else:
                print(f"Unknown command: {command}")
                # For unknown commands, just echo back the command byte
                self.send_response(command)

        except Exception as e:
            print(f"Error processing command {command}: {e}")

    def send_response(self, command, data=b""):
        """Send a response in the proper protocol format"""
        if self.serial and self.serial.is_open:
            response = bytes([0xAA, command]) + data
            self.serial.write(response)

    def generate_measurement(self):
        """Generate realistic fake measurement data"""
        # This is now handled in the command 72 processing
        pass


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

        print("Fake LCR Meter E7-28 simulator is running. Press Ctrl+C to stop.")
        print("Implemented commands: 64, 65, 66, 67, 70, 71, 72")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        meter.stop()


if __name__ == "__main__":
    main()
