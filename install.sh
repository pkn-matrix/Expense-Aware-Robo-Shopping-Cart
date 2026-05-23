#!/bin/bash
# ─────────────────────────────────────────────
#  install.sh — Smart Cart Setup Script
#  Run this once on your Raspberry Pi
#  Usage: bash install.sh
# ─────────────────────────────────────────────

echo "================================================"
echo "   🛒  Smart Cart — Installation Script"
echo "================================================"

# ── Step 1: System Update ────────────────────
echo ""
echo "[1/5] Updating system packages..."
sudo apt update -y
sudo apt upgrade -y

# ── Step 2: System Libraries ─────────────────
echo ""
echo "[2/5] Installing system libraries..."
sudo apt install -y \
    libzbar0 \
    python3-pip \
    python3-dev \
    libatlas-base-dev \
    libjpeg-dev \
    libopenjp2-7 \
    v4l-utils \
    chromium-browser

# Add user to serial/dialout group
sudo usermod -a -G dialout $USER
echo "Added $USER to dialout group (Arduino serial access)"

# ── Step 3: Enable Camera ─────────────────────
echo ""
echo "[3/5] Enabling Raspberry Pi camera..."
sudo raspi-config nonint do_camera 0
echo "Camera enabled!"

# ── Step 4: PyTorch (ARM) ─────────────────────
echo ""
echo "[4/5] Installing PyTorch for Raspberry Pi..."
echo "This may take 10-20 minutes..."
pip install torch torchvision \
    --index-url https://download.pytorch.org/whl/cpu \
    --break-system-packages

# ── Step 5: Python Libraries ──────────────────
echo ""
echo "[5/5] Installing Python libraries..."
pip install -r requirements.txt --break-system-packages

# ── Step 6: Auto-launch Setup ─────────────────
echo ""
echo "[6/6] Setting up auto-launch on boot..."

# Copy systemd service
sudo cp smartcart.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable smartcart

# Create desktop shortcut
mkdir -p /home/$USER/.config/autostart
cat > /home/$USER/.config/autostart/smartcart-browser.desktop << EOF
[Desktop Entry]
Type=Application
Name=SmartCart Browser
Exec=bash -c 'sleep 15 && chromium-browser --kiosk --noerrdialogs --disable-infobars http://localhost:5000'
Hidden=false
X-GNOME-Autostart-enabled=true
EOF

# Create desktop icon
cat > /home/$USER/Desktop/SmartCart.desktop << EOF
[Desktop Entry]
Name=🛒 Smart Cart
Comment=Start Smart Cart System
Exec=bash -c 'cd /home/$USER/smart_cart && python3 app.py'
Icon=applications-other
Terminal=false
Type=Application
EOF
chmod +x /home/$USER/Desktop/SmartCart.desktop

# ── Verify Installation ───────────────────────
echo ""
echo "================================================"
echo "   Verifying Installation..."
echo "================================================"
python3 -c "
import sys
libs = ['flask', 'flask_socketio', 'gevent', 'cv2', 'ultralytics', 'pyzbar', 'serial', 'PIL']
all_ok = True
for lib in libs:
    try:
        __import__(lib)
        print(f'  ✅  {lib}')
    except ImportError as e:
        print(f'  ❌  {lib} — {e}')
        all_ok = False
print()
if all_ok:
    print('All libraries installed successfully!')
else:
    print('Some libraries failed. Check errors above.')
"

echo ""
echo "================================================"
echo "   ✅  Installation Complete!"
echo "================================================"
echo ""
echo "  Next steps:"
echo "  1. Upload arduino/smart_cart.ino to Arduino"
echo "  2. Connect Arduino to Pi via USB"
echo "  3. Reboot: sudo reboot"
echo "  4. Cart starts automatically on boot!"
echo ""
echo "  Or run manually:"
echo "  cd /home/$USER/smart_cart && python3 app.py"
echo "================================================"
