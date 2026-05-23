<p align="center">
  <b>🛠️ Hardware Prototyping & System Integration</b>
</p>

<table align="center">
  <tr>
    <td align="center" width="50%">
      <img src="https://github.com/user-attachments/assets/efd8b731-eaa6-4d69-832e-980ba7a623b4" width="95%" alt="Base Framework"><br>
      <sub><b>Base Framework</b></sub>
    </td>
    <td align="center" width="50%">
      <img src="https://github.com/user-attachments/assets/972678e3-d918-4742-976b-8ea40d1160c5" width="95%" alt="Sensor Alignment"><br>
      <sub><b>Hardware Implementation</b></sub>
    </td>
  </tr>
  <tr>
    <td align="center" width="50%">
      <img src="https://github.com/user-attachments/assets/d2066146-5bd3-4f16-8742-83fdc582a477" width="95%" alt="Drivetrain Overview"><br>
      <sub><b>Drivetrain Overview</b></sub>
    </td>
    <td align="center" width="50%">
      <img src="https://github.com/user-attachments/assets/5d08eaa9-e2a4-45eb-a8d3-79bdd238a1cc" width="95%" alt="Circuit Framework"><br>
      <sub><b>Circuit Diagram Schematic</b></sub>
    </td>
  </tr>
</table>

<p align="center">
  <img src="https://github.com/user-attachments/assets/d2b4cee0-3b55-491e-8cd4-7652361624ee" width="65%" alt="System Integration"><br>
  <sub><b>System Architecture Flowchart</b></sub>
</p>

---

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
