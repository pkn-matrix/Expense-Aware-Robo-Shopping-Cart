# ─────────────────────────────────────────────
#  obstacle.py — Arduino Serial Communication
#  Smart Cart Project — FIXED VERSION
# ─────────────────────────────────────────────

import serial
import serial.tools.list_ports
import time

# ── Settings ─────────────────────────────────
BAUD_RATE    = 9600
TIMEOUT      = 1       # seconds

arduino      = None
DEMO_MODE    = False   # True if Arduino not connected

def find_arduino_port():
    """
    Auto-detect Arduino serial port.
    Checks common Pi ports automatically.
    """
    common_ports = ['/dev/ttyUSB0', '/dev/ttyUSB1',
                    '/dev/ttyACM0', '/dev/ttyACM1']

    # Try common ports first
    for port in common_ports:
        try:
            s = serial.Serial(port, BAUD_RATE, timeout=0.5)
            s.close()
            print(f"[ARDUINO] Found on {port}")
            return port
        except serial.SerialException:
            continue

    # Auto-scan all ports
    ports = serial.tools.list_ports.comports()
    for port in ports:
        if 'USB' in port.description or 'Arduino' in port.description:
            print(f"[ARDUINO] Auto-detected: {port.device}")
            return port.device

    return None

def connect_arduino():
    """
    Initialize serial connection to Arduino.
    Returns True if connected, False if not found (demo mode).
    """
    global arduino, DEMO_MODE

    port = find_arduino_port()

    if port is None:
        print("[ARDUINO] ⚠️  Not found — running in DEMO MODE")
        print("[ARDUINO]    Cart logic will run without hardware")
        DEMO_MODE = True
        return False

    try:
        arduino = serial.Serial(port, BAUD_RATE, timeout=TIMEOUT)
        time.sleep(2)   # Wait for Arduino to reset after connect
        print(f"[ARDUINO] ✅ Connected on {port}")
        DEMO_MODE = False
        return True
    except serial.SerialException as e:
        print(f"[ARDUINO] ❌ Connection failed: {e}")
        DEMO_MODE = True
        return False

def send_command(cmd):
    """
    Send a single character command to Arduino.
    Commands: F=Forward B=Backward L=Left R=Right S=Stop
    """
    global arduino, DEMO_MODE

    if DEMO_MODE:
        print(f"[DEMO] Command: {cmd}")
        return

    if arduino and arduino.is_open:
        try:
            arduino.write(cmd.encode())
        except serial.SerialException as e:
            print(f"[ARDUINO] Send error: {e}")
            # Try to reconnect
            connect_arduino()
    else:
        print(f"[ARDUINO] Not connected — reconnecting...")
        connect_arduino()

def check_obstacle():
    """
    Check if Arduino reported an obstacle.
    Returns True if obstacle detected.
    """
    global arduino, DEMO_MODE

    if DEMO_MODE:
        return False

    if arduino and arduino.in_waiting:
        try:
            data = arduino.readline().decode('utf-8', errors='ignore').strip()
            if "OBSTACLE" in data:
                print("[OBSTACLE] ⚠️  Detected! Stopping cart.")
                return True
        except Exception as e:
            print(f"[ARDUINO] Read error: {e}")
    return False

def disconnect_arduino():
    """Safely close serial connection."""
    global arduino
    if arduino and arduino.is_open:
        send_command('S')   # Stop cart first
        time.sleep(0.2)
        arduino.close()
        print("[ARDUINO] Disconnected safely")
