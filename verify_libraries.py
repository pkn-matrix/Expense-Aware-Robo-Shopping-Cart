#!/usr/bin/env python3
# ─────────────────────────────────────────────
#  verify_libraries.py — Library Check Script
#  Run this AFTER install.sh to verify everything
#  Usage: python3 verify_libraries.py
# ─────────────────────────────────────────────

import sys

print("=" * 48)
print("  🔍  Smart Cart — Library Verification")
print("=" * 48)

checks = [
    ("flask",          "Flask web framework"),
    ("flask_socketio", "Flask-SocketIO real-time"),
    ("gevent",         "Gevent async mode"),
    ("cv2",            "OpenCV camera"),
    ("ultralytics",    "YOLOv8 detection"),
    ("pyzbar",         "Barcode reader"),
    ("serial",         "PySerial Arduino"),
    ("PIL",            "Pillow image processing"),
]

all_passed = True

for lib, description in checks:
    try:
        module = __import__(lib)
        version = getattr(module, '__version__', 'unknown')
        print(f"  ✅  {description:<30} ({version})")
    except ImportError as e:
        print(f"  ❌  {description:<30} MISSING — {e}")
        all_passed = False

print()

# Extra checks
print("── Extra Checks ─────────────────────────")

# Check camera
try:
    import cv2
    cap = cv2.VideoCapture(0)
    if cap.isOpened():
        print("  ✅  Camera detected and accessible")
        cap.release()
    else:
        print("  ⚠️   Camera not found (check ribbon cable)")
except Exception as e:
    print(f"  ❌  Camera error: {e}")

# Check serial ports
try:
    import serial.tools.list_ports
    ports = list(serial.tools.list_ports.comports())
    if ports:
        for p in ports:
            print(f"  ✅  Serial port: {p.device} ({p.description})")
    else:
        print("  ⚠️   No serial ports found (Arduino not connected?)")
except Exception as e:
    print(f"  ❌  Serial port check error: {e}")

# Check Python version
ver = sys.version_info
print(f"  ✅  Python {ver.major}.{ver.minor}.{ver.micro}")

print()
print("=" * 48)
if all_passed:
    print("  ✅  All libraries OK! Ready to run.")
    print("  ▶   Start with: python3 app.py")
else:
    print("  ❌  Some libraries missing!")
    print("  ▶   Run: bash install.sh")
print("=" * 48)
