# ─────────────────────────────────────────────
#  scanner.py — Barcode + YOLO Product Scanner
#  Smart Cart Project — FIXED VERSION
# ─────────────────────────────────────────────

import cv2
from pyzbar.pyzbar import decode
from ultralytics import YOLO
from database import get_product

# Load YOLO model once at startup (saves time)
print("[SCANNER] Loading YOLO model...")
model = YOLO("yolov8n.pt")   # nano = fastest on Pi
print("[SCANNER] YOLO model ready")

def scan_barcode(frame):
    """
    Try to read a barcode from a camera frame.
    Returns product dict or None.
    """
    try:
        barcodes = decode(frame)
        for barcode in barcodes:
            data = barcode.data.decode("utf-8")
            product = get_product(data)
            if product:
                print(f"[BARCODE] ✅ Found: {product['name']} @ ${product['price']}")
                return product
            else:
                print(f"[BARCODE] ⚠️ Unknown barcode: {data}")
    except Exception as e:
        print(f"[BARCODE] Error: {e}")
    return None

def detect_with_yolo(frame):
    """
    Use YOLO to visually identify a product.
    Returns product dict with price 0.00 if found.
    """
    try:
        # Resize to 320x240 for faster processing on Pi
        small_frame = cv2.resize(frame, (320, 240))
        results = model(small_frame, verbose=False)

        for result in results:
            for box in result.boxes:
                confidence = float(box.conf)
                if confidence > 0.5:
                    label = result.names[int(box.cls)]
                    print(f"[YOLO] ✅ Detected: {label} ({confidence:.0%} confident)")
                    return {"name": label, "price": 0.00}
    except Exception as e:
        print(f"[YOLO] Error: {e}")
    return None

def scan_product(frame):
    """
    Main scan function — called every 3 seconds by app.py
    1. Try barcode first (faster & more accurate)
    2. Fall back to YOLO visual detection
    Returns product dict or None.
    """
    # Step 1 — Barcode scan
    product = scan_barcode(frame)
    if product:
        return product

    # Step 2 — YOLO fallback
    product = detect_with_yolo(frame)
    if product:
        return product

    return None
