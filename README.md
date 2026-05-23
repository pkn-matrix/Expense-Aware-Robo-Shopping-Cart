## 🚀 Features
* **Autonomous Shopper Following:** Utilizes sensor-driven navigation to safely follow a user through market aisles.
* **Real-Time Expense Tracking:** Automatically logs items as they are added to the cart and displays a running total.
* **Smart Power & Motion Control:** Integrated motor drivers and chassis design optimized for varying grocery payloads.

---

## 🛠️ Hardware Architecture
The system uses a master-slave configuration to split heavy computation and low-level hardware control:

* **Master Controller (Raspberry Pi 5):** Handles data processing, the tracking logic, user interface, and expense logging.
* **Slave Controller (Arduino):** Manages real-time sensor data collection and sends PWM signals to the motor drivers.
* **Drivetrain:** 4WD robotic chassis powered by DC geared motors, designed to handle rolling and grade resistance under load.

---

## 💻 Tech Stack
* **Languages:** Python (Raspberry Pi), C++ (Arduino)
* **Frameworks/Libraries:** `pyserial` (for Pi-to-Arduino communication)

---

## 📅 Project Roadmap
- [x] Assemble the 4WD chassis and configure the DC geared motors. (Code initialized in [arduino/](arduino))
- [x] Establish stable serial communication between the Raspberry Pi 5 and Arduino. (Implemented via `pyserial` in [app.py](app.py))
- [x] Implement the basic autonomous following algorithm. (Developed in [human_following.py](human_following.py))
- [x] Integrate the item tracking module and expense calculator UI. (Configured in [scanner.py](scanner.py) and [templates/](templates))
