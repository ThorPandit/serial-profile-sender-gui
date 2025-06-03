# serial-profile-sender-gui
A Python-based GUI tool for automating serial communication with embedded modules. Supports profile-based command execution, real-time log monitoring, HEX/ASCII modes, and editable test sequences. Ideal for NIC/module testing and validation workflows.

# Serial Command Logger & Profile Executor

A Python-based GUI tool to automate serial communication with embedded devices (like NICs or modules). It supports sending sequences of commands defined in user-configurable profiles, real-time log monitoring, HEX/ASCII modes, and live COM port management.
---

## 🚀 Features
- 🔌 Connect to serial ports with adjustable baud rate
- 🧰 Create, edit, and delete command profiles
- 📜 Define step-by-step command sequences with custom delays
- 🔄 Support for both ASCII and HEX mode transmissions
- 🪵 Real-time log display for received and sent data
- 📤 Execute saved profiles on connected serial devices
- 🧠 Profile persistence using JSON
---

## 📸 Screenshot
![image](https://github.com/user-attachments/assets/79f4c6cf-b321-4bd2-9098-266a57221c2d) 
---

### Requirements
- Python 3.7+
- `pyserial`
- `tkinter`

### Setup
```bash
git clone https://github.com/yourusername/serial-profile-sender-gui.git
cd serial-profile-sender-gui
pip install -r requirements.txt
python app.py

