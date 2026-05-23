# ─────────────────────────────────────────────
#  app.py — Main Flask Web App + Cart Controller
#  Smart Cart Project — FIXED VERSION
#  Fix: gevent instead of eventlet (Python 3.12 safe)
# ─────────────────────────────────────────────

from gevent import monkey
monkey.patch_all()   # Must be FIRST before other imports

from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import threading
import cv2
import time

from scanner         import scan_product
from human_following import get_follow_command
from obstacle        import (connect_arduino, send_command,
                             check_obstacle, disconnect_arduino)
from database        import products, add_product
import base64, io, os

# ── Flask App Setup ──────────────────────────
app = Flask(__name__)
app.config['SECRET_KEY'] = 'smartcart2024'

# FIX: Use gevent (works on Python 3.11 & 3.12)
socketio = SocketIO(app,
    cors_allowed_origins="*",
    async_mode='gevent',
    ping_timeout=60,
    ping_interval=25)

# ── Cart State ───────────────────────────────
cart = {
    "items"  : [],
    "total"  : 0.0,
    "budget" : 0.0,
    "status" : "⚙️ Please set a budget",
    "color"  : "blue",
    "mode"   : "FOLLOWING"
    # Modes:
    # FOLLOWING → cart follows person (YOLO active)
    # BILLING   → cart stopped, person detection OFF
    # STOPPED   → cart stopped, person detection OFF
}

# ── Routes ───────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/barcodes")
def barcodes_page():
    return render_template("barcodes.html")

@app.route("/video_feed")
def video_feed():
    """MJPEG stream — live camera feed shown inside scan modal."""
    from flask import Response
    def generate():
        cap = cv2.VideoCapture(0)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH,  640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                _, jpeg = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' +
                       jpeg.tobytes() + b'\r\n')
        finally:
            cap.release()
    return Response(generate(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

# ── Manual Scan Socket Event ─────────────────
@socketio.on("manual_scan")
def handle_manual_scan():
    """
    Triggered by the UI scan button.
    Captures one frame, tries barcode + YOLO, emits result.
    """
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    try:
        ret, frame = cap.read()
        if not ret:
            emit("scan_error", {"message": "Camera not available"})
            return

        product = scan_product(frame)
        if product:
            add_scanned_item(product["name"], product["price"])
            emit("scan_result", {
                "found": True,
                "name" : product["name"],
                "price": product["price"]
            })
        else:
            emit("scan_result", {"found": False})
    except Exception as e:
        emit("scan_error", {"message": str(e)})
    finally:
        cap.release()

# ── Barcode Manager Socket Events ────────────
@socketio.on("get_products")
def handle_get_products():
    emit("products_data", products)

@socketio.on("add_product")
def handle_add_product(data):
    try:
        name    = str(data["name"]).strip()
        price   = round(float(data["price"]), 2)
        barcode = str(data["barcode"]).strip()
        if name and price >= 0 and barcode:
            add_product(barcode, name, price)
            emit("product_added", {"name": name})
        else:
            emit("error_msg", {"message": "Invalid product data"})
    except Exception as e:
        emit("error_msg", {"message": str(e)})

@socketio.on("delete_product")
def handle_delete_product(data):
    try:
        barcode = data["barcode"]
        if barcode in products:
            name = products[barcode]["name"]
            del products[barcode]
            emit("product_deleted", {"name": name})
        else:
            emit("error_msg", {"message": "Product not found"})
    except Exception as e:
        emit("error_msg", {"message": str(e)})

@socketio.on("get_barcode_image")
def handle_get_barcode_image(data):
    """Generate barcode image and send as base64."""
    try:
        import barcode as bc
        from barcode.writer import ImageWriter

        barcode_num = data["barcode"]
        digits = ''.join(filter(str.isdigit, barcode_num))[:12].ljust(12, '0')

        buffer = io.BytesIO()
        ean    = bc.get('ean13', digits, writer=ImageWriter())
        ean.write(buffer, options={
            "module_width" : 0.25,
            "module_height": 12.0,
            "font_size"    : 8,
            "quiet_zone"   : 4.0,
            "write_text"   : True,
        })
        buffer.seek(0)
        img_b64 = base64.b64encode(buffer.read()).decode('utf-8')
        emit("barcode_image", {"barcode": barcode_num, "image": img_b64})
    except Exception as e:
        emit("error_msg", {"message": f"Barcode image error: {e}"})

@socketio.on("generate_pdf")
def handle_generate_pdf():
    """Trigger full PDF generation."""
    try:
        import subprocess
        subprocess.Popen(["python3", "barcode_generator.py"])
        emit("generate_pdf_done", {"message": "PDF generation started"})
    except Exception as e:
        emit("error_msg", {"message": f"PDF error: {e}"})

# ── Socket Events ────────────────────────────
@socketio.on("connect")
def on_connect():
    print("[UI] Client connected")
    push_cart_update()   # Send current state on connect

@socketio.on("disconnect")
def on_disconnect():
    print("[UI] Client disconnected")

@socketio.on("set_budget")
def handle_set_budget(data):
    try:
        cart["budget"] = round(float(data["budget"]), 2)
        print(f"[UI] Budget set: ${cart['budget']:.2f}")
        push_cart_update()
    except (ValueError, KeyError) as e:
        print(f"[UI] Budget error: {e}")

@socketio.on("remove_item")
def handle_remove_item(data):
    try:
        index = int(data["index"])
        if 0 <= index < len(cart["items"]):
            removed = cart["items"].pop(index)
            cart["total"] = round(
                max(0.0, cart["total"] - removed["price"]), 2)
            print(f"[UI] Removed: {removed['name']}")
            push_cart_update()
    except (ValueError, KeyError, IndexError) as e:
        print(f"[UI] Remove error: {e}")

@socketio.on("clear_cart")
def handle_clear_cart():
    cart["items"] = []
    cart["total"] = 0.0
    print("[UI] Cart cleared")
    push_cart_update()

@socketio.on("toggle_mode")
def handle_toggle_mode():
    """Cycle: FOLLOWING → BILLING → FOLLOWING"""
    if cart["mode"] == "FOLLOWING":
        cart["mode"] = "BILLING"
        send_command('S')
        print("[MODE] → BILLING (person detection OFF)")
    else:
        cart["mode"] = "FOLLOWING"
        print("[MODE] → FOLLOWING (person detection ON)")
    socketio.emit("mode_update", {"mode": cart["mode"]})

@socketio.on("set_billing_mode")
def handle_set_billing_mode():
    """Explicitly switch to BILLING mode from UI scan button."""
    cart["mode"] = "BILLING"
    send_command('S')
    print("[MODE] → BILLING — scan button pressed, stopping person detection")
    socketio.emit("mode_update", {"mode": cart["mode"]})

@socketio.on("set_following_mode")
def handle_set_following_mode():
    """Return to FOLLOWING mode after billing is done."""
    cart["mode"] = "FOLLOWING"
    print("[MODE] → FOLLOWING — billing closed, resuming person detection")
    socketio.emit("mode_update", {"mode": cart["mode"]})

# ── Cart Update Broadcaster ──────────────────
def push_cart_update():
    """Calculate budget status and push to all UI clients."""
    budget    = cart["budget"]
    total     = cart["total"]
    remaining = round(budget - total, 2)

    if budget == 0:
        status = "⚙️ Please set a budget"
        color  = "blue"
    elif total > budget:
        status = "🚨 OVER BUDGET!"
        color  = "red"
    elif total >= budget * 0.9:
        status = "⚠️ Approaching Limit!"
        color  = "orange"
    else:
        status = "✅ Within Budget"
        color  = "green"

    cart["status"] = status
    cart["color"]  = color

    socketio.emit("cart_update", {
        "items"    : cart["items"],
        "total"    : total,
        "budget"   : budget,
        "remaining": remaining,
        "status"   : status,
        "color"    : color
    })

def add_scanned_item(name, price):
    """Add a scanned product to cart and update UI."""
    cart["items"].append({
        "name" : name,
        "price": round(float(price), 2)
    })
    cart["total"] = round(cart["total"] + float(price), 2)
    print(f"[SCAN] ✅ Added: {name} @ ${price:.2f} | Total: ${cart['total']:.2f}")
    push_cart_update()

# ── Cart Controller (Background Thread) ──────
def cart_controller():
    """
    Runs in background thread:
    - Human following
    - Obstacle detection & avoidance
    - Product scanning every 3 seconds
    """
    # Open camera
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 15)   # Limit FPS to save CPU

    if not cap.isOpened():
        print("[CAMERA] ❌ Failed to open camera!")
        print("[CAMERA]    Check: sudo raspi-config → Interface → Camera → Enable")
        return

    print("[CART] ✅ Controller started")
    last_scan_time = 0
    frame_skip     = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            time.sleep(0.1)
            continue

        # ── Safety: Obstacle Check ────────────
        if check_obstacle():
            send_command('S')
            time.sleep(0.5)
            continue

        # ── Mode: FOLLOWING ───────────────────
        # Person detection ON — cart follows customer
        if cart["mode"] == "FOLLOWING":
            frame_skip += 1
            if frame_skip % 2 == 0:
                cmd = get_follow_command(frame)
                send_command(cmd)

        # ── Mode: BILLING ─────────────────────
        # Person detection OFF — cart stays still
        # Customer is scanning products at billing counter
        elif cart["mode"] == "BILLING":
            send_command('S')   # Stay completely still
            # No YOLO, no human_following — saves CPU too

        # ── Mode: STOPPED ─────────────────────
        else:
            send_command('S')

        time.sleep(0.1)   # ~10Hz loop

    cap.release()
    print("[CART] Controller stopped")

# ── Main Entry Point ─────────────────────────
if __name__ == "__main__":
    print("=" * 48)
    print("   🛒  Smart Cart System — Starting Up")
    print("=" * 48)

    # Connect to Arduino (auto-detects port)
    if connect_arduino():
        print("[SYSTEM] ✅ Arduino connected")
    else:
        print("[SYSTEM] ⚠️  Running in demo mode (no Arduino)")

    # Start cart controller in background
    cart_thread = threading.Thread(
        target=cart_controller,
        daemon=True,
        name="CartController"
    )
    cart_thread.start()
    print("[SYSTEM] ✅ Cart controller running")
    print("[SYSTEM] 🌐 Web UI → http://localhost:5000")
    print("=" * 48)

    # Start web server
    try:
        socketio.run(app,
            host="0.0.0.0",
            port=5000,
            debug=False,
            use_reloader=False)
    except KeyboardInterrupt:
        print("\n[SYSTEM] Shutting down...")
    finally:
        disconnect_arduino()
        print("[SYSTEM] Goodbye!")
