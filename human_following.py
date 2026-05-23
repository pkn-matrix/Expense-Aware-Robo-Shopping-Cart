# ─────────────────────────────────────────────
#  human_following.py — Person Tracking Logic
#  Smart Cart Project — FIXED VERSION
# ─────────────────────────────────────────────

import cv2
from ultralytics import YOLO

# Load YOLO model once (shared with scanner if needed)
print("[FOLLOW] Loading YOLO person model...")
model = YOLO("yolov8n.pt")
print("[FOLLOW] Model ready")

# ── Frame Zone Settings ───────────────────────
FRAME_WIDTH  = 640
CENTER_MIN   = 210    # Left boundary of center zone
CENTER_MAX   = 430    # Right boundary of center zone

# ── Distance Thresholds (bounding box height px) ─
TOO_CLOSE    = 225    # If taller than this → move back
TOO_FAR      = 90     # If shorter than this → move forward

# ── Search counter ────────────────────────────
lost_counter = 0
MAX_SEARCH   = 25     # Frames before giving up search

def get_follow_command(frame):
    """
    Analyze frame and return movement command char:
      F = Forward
      B = Backward
      L = Turn Left
      R = Turn Right
      S = Stop
    """
    global lost_counter

    try:
        # Resize for faster processing on Pi
        small = cv2.resize(frame, (320, 240))
        results = model(small, classes=[0], verbose=False)  # Class 0 = Person only

        for result in results:
            for box in result.boxes:
                confidence = float(box.conf)
                if confidence < 0.5:
                    continue

                # Scale box back to original frame size
                x1, y1, x2, y2 = box.xyxy[0]
                x1 = int(x1 * 2); x2 = int(x2 * 2)
                y1 = int(y1 * 2); y2 = int(y2 * 2)

                box_height = y2 - y1
                center_x   = (x1 + x2) // 2
                lost_counter = 0   # Reset — person found

                # ── Too close → back up ──────
                if box_height > TOO_CLOSE:
                    return 'B'

                # ── Too far → move toward ────
                elif box_height < TOO_FAR:
                    if center_x < CENTER_MIN:
                        return 'L'
                    elif center_x > CENTER_MAX:
                        return 'R'
                    else:
                        return 'F'

                # ── Good distance → align ────
                else:
                    if center_x < CENTER_MIN:
                        return 'L'
                    elif center_x > CENTER_MAX:
                        return 'R'
                    return 'S'

    except Exception as e:
        print(f"[FOLLOW] Error: {e}")

    # ── No person detected ───────────────────
    lost_counter += 1

    if lost_counter < 10:
        return 'S'              # Wait briefly
    elif lost_counter < MAX_SEARCH:
        return 'R'              # Rotate slowly to search
    else:
        lost_counter = 0
        return 'S'              # Give up — stop
