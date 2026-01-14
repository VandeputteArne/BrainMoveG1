# BrainMoveAJM: Rpi 5 Setup Guide

**Table of Contents**

* [1. Project Configuration](#1-project-configuration)
* [2. Quick Reference (True Copy-Paste)](#2-quick-reference-true-copy-paste)
  * [A. Set Static Eth0 IP](#a-set-static-eth0-ip)
  * [B. Update System](#b-update-system)
  * [C. Disable Internal Bluetooth](#c-disable-internal-bluetooth)
  * [D. Unblock WiFi & Bluetooth](#d-unblock-wifi--bluetooth-if-needed)
  * [E. Setup Hotspot](#e-setup-hotspot-wlan1)
  * [F. Bluetooth Pairing](#f-bluetooth-pairing-esp32-c3)
* [3. Detailed Setup Steps](#3-detailed-setup-steps)
  * [Phase 1: PC & OS Prep](#phase-1-pc--os-prep)
  * [Phase 2: Set Static Eth0 IP](#phase-2-set-static-eth0-ip)
  * [Phase 3: Update System](#phase-3-update-system)
  * [Phase 4: Disable Internal Bluetooth](#phase-4-disable-internal-bluetooth)
  * [Phase 5: Unblock WiFi & Bluetooth](#phase-5-unblock-wifi--bluetooth)
  * [Phase 6: Setup Hotspot (wlan1)](#phase-6-setup-hotspot-wlan1)
  * [Phase 7: Bluetooth Pairing](#phase-7-bluetooth-pairing-esp32-c3)
* [4. Verification (Python Script)](#4-verification-python-script)

---

## 1. Project Configuration

| Category | Setting | Value |
| --- | --- | --- |
| **Credentials** | Hostname | `BrainMoveAJM` |
|  | User | `bmajm` |
|  | Password | `secureajm5!` |
| **Ethernet** | Static IP | `192.168.137.50/24` |
|  | Gateway (PC) | `192.168.137.1` |
|  | DNS | `8.8.8.8` |
| **Hotspot** | SSID | `BrainMoveAJM` |
|  | Password | `bmSecure1998` |
| **Hardware** | Bluetooth | TP-Link UB500 (External) |

---

## 2. Quick Reference (True Copy-Paste)

You can paste these blocks directly into your terminal. They execute the actions **automatically** (no editors).

**SSH Login:**

```bash
ssh bmajm@BrainMoveAJM.local
# Password: secureajm5!

```

**A. Set Static Eth0 IP**

```bash
sudo nmcli con mod "Wired connection 1" ipv4.addresses 192.168.137.50/24 ipv4.gateway 192.168.137.1 ipv4.dns 8.8.8.8 ipv4.method manual
sudo nmcli con down "Wired connection 1" && sudo nmcli con up "Wired connection 1"

# (Optional) Share internet from eth0 or connect to WiFi on wlan0 to get internet access:
sudo nmcli connection modify "Wired connection 1" ipv4.never-default yes
sudo ip route del default via 192.168.137.1

```

**B. Update System**

```bash
sudo apt update && sudo apt full-upgrade -y

```

**C. Disable Internal Bluetooth**

```bash
echo "dtoverlay=disable-bt" | sudo tee -a /boot/firmware/config.txt
sudo reboot

```

**D. Unblock WiFi & Bluetooth (if needed)**

```bash
sudo rfkill unblock wifi
sudo rfkill unblock bluetooth
```

**E. Setup Hotspot (wlan1)**

```bash
sudo raspi-config nonint do_wifi_country BE
sudo nmcli con add type wifi ifname wlan1 con-name "BrainMoveAJM" autoconnect yes ssid "BrainMoveAJM" mode ap ipv4.method shared wifi-sec.key-mgmt wpa-psk wifi-sec.psk "bmSecure1998"
sudo nmcli connection up "BrainMoveAJM"

```

**F. Finding MAC addresses (ESP32-C3)**

```bash
sudo bluetoothctl
# Inside the tool:
agent on
default-agent
scan on
# Wait for MAC address...
connect XX:XX:XX:XX:XX:XX
trust XX:XX:XX:XX:XX:XX
pair XX:XX:XX:XX:XX:XX
scan off

```

**G. Clone Project Repo**

```bash
git clone # <REPO_URL>
```

**H. Install Package Dependencies**

```bash
cd BrainMove/BrainMoveG1
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**I. Set start on boot (systemd)**

```bash
sudo cp ./devices/rpi5/brainmoveajm.service /etc/systemd/system/
sudo systemctl enable brainmoveajm.service
```

**J. Reboot to Apply All Changes**

```bash
sudo reboot
```

---

## 3. Detailed Setup Steps

### Phase 1: PC & OS Prep

1. **Windows Internet Sharing (ICS):**
* Go to Network Connections (`ncpa.cpl`).
* Right-click on your WiFi adapter -> Properties -> Sharing.
* Check "Allow other network users to connect...".
* Select the Ethernet adapter that the Pi is connected to.
* *Result:* Windows automatically sets the Ethernet adapter to `192.168.137.1`.

2. **Flash OS:**
* Use Raspberry Pi Imager.
* OS: Raspberry Pi OS (64-bit) Bookworm.
* Settings: Hostname `BrainMoveAJM`, User `bmajm`, Pass `secureajm5!`, **Enable SSH**.

### Phase 2: Set Static Eth0 IP

Configure Ethernet with a static IP address (`192.168.137.50/24`) so you always have reliable SSH access:

```bash
sudo nmcli con mod "Wired connection 1" ipv4.addresses 192.168.137.50/24 ipv4.gateway 192.168.137.1 ipv4.dns 8.8.8.8 ipv4.method manual
sudo nmcli con down "Wired connection 1" && sudo nmcli con up "Wired connection 1"
```

**Why static IP?** Instead of DHCP (dynamic IP that changes), a static IP ensures the Pi always has the same address, making it reliable for SSH and network communication.

### Phase 3: Update System

Update all system packages:

```bash
sudo apt update && sudo apt full-upgrade -y
```

**Why updates?** Brings in security patches, bug fixes, and new features. `full-upgrade` handles dependency changes (safer than `upgrade`).

### Phase 4: Disable Internal Bluetooth

The RPi 5 internal Bluetooth causes massive interference. We force the TP-Link dongle to be primary by disabling the internal Bluetooth:

```bash
echo "dtoverlay=disable-bt" | sudo tee -a /boot/firmware/config.txt
sudo reboot
```

The command writes this directly to the config file, so after reboot you're guaranteed that `hci0` is your TP-Link dongle (verify with `hciconfig -a`, look for "Realtek").

### Phase 5: Unblock WiFi & Bluetooth

If WiFi or Bluetooth are blocked by rfkill (software radio block), unblock them:

```bash
sudo rfkill unblock wifi
sudo rfkill unblock bluetooth
```

**Why unblock?** Sometimes the system blocks wireless interfaces to save power or due to hardware switches. This ensures both WiFi and Bluetooth are available for use.

### Phase 6: Setup Hotspot (wlan1)

Transform the WiFi adapter (wlan1 - external USB adapter) into an access point (hotspot) so other devices can connect to the Pi wirelessly:

```bash
sudo raspi-config nonint do_wifi_country BE
sudo nmcli con add type wifi ifname wlan1 con-name "BrainMoveAJM" autoconnect yes ssid "BrainMoveAJM" mode ap ipv4.method shared wifi-sec.key-mgmt wpa-psk wifi-sec.psk "bmSecure1998"
sudo nmcli connection up "BrainMoveAJM"
```

# (Optional) Share internet from eth0 or connect to WiFi on wlan0 to get internet access:

```bash
sudo nmcli connection modify "Wired connection 1" ipv4.never-default yes
sudo ip route del default via 192.168.137.1
```

**Parameters:**
- `ifname wlan1` - Use external WiFi adapter (TP-Link or similar USB WiFi dongle)
- `mode ap` - Access point mode (broadcast WiFi signal)
- `ipv4.method shared` - Enable DHCP server so devices get IPs automatically
- `wifi-sec.psk "bmSecure1998"` - WiFi password

### Phase 7: Finding MAC addresses (ESP32-C3)

```bash
sudo bluetoothctl
# Inside the tool:
agent on
default-agent
scan on
# Wait for MAC address...
connect XX:XX:XX:XX:XX:XX
trust XX:XX:XX:XX:XX:XX
pair XX:XX:XX:XX:XX:XX
scan off
```

### Phase 8: Clone Project Repo

Clone the project repository to the Pi:

```bash
git clone # <REPO_URL>
```

### Phase 9: Install Package Dependencies

Set up the Python environment and install required packages:

```bash
cd BrainMove/BrainMoveG1
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Why virtual environment?** Isolates project dependencies from system Python packages, preventing version conflicts.

### Phase 10: Set Start on Boot (systemd)

Configure the service to start automatically on boot:

```bash
sudo cp ./devices/rpi5/brainmoveajm.service /etc/systemd/system/
sudo systemctl enable brainmoveajm.service
```

**Why systemd?** Ensures the BrainMove application starts automatically when the Pi boots, making it reliable for headless operation.

### Phase 11: Reboot to Apply All Changes

Reboot the system to finalize all configurations:

```bash
sudo reboot
```

---

## 4. Verification (Python Script)

To verify that the connection works without using `bluetoothctl`, use this test script.

**Install library:**

```bash
sudo apt install python3-pip -y
python3 -m venv myenv
source myenv/bin/activate
pip install bleak

```

**Create script (`test_ble.py`):**

```python
import asyncio
from bleak import BleakClient

# REPLACE THIS WITH YOUR ESP32 MAC ADDRESS
ADDRESS = "XX:XX:XX:XX:XX:XX"

async def main():
    print(f"Connecting to {ADDRESS}...")
    try:
        async with BleakClient(ADDRESS) as client:
            print(f"Connected: {client.is_connected}")
            for service in client.services:
                print(f"[Service] {service.uuid}")
                for char in service.characteristics:
                    print(f"  - [Char] {char.uuid}")
    except Exception as e:
        print(f"Error: {e}")

asyncio.run(main())

```

**Run:**

```bash
python test_ble.py

```

If this prints `Connected: True`, your system is perfectly configured.