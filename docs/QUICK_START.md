# DeviceManager & ESP32Device - Simple Workflow

Quick reference for the basic usage flow.

---

## Basic Workflow

```
1. Create DeviceManager
   ↓
2. Set Callbacks (optional)
   ↓
3. Scan for Devices
   ↓
4. Connect All
   ↓
5. Start Polling
   ↓
6. Receive Events (via callbacks)
   ↓
7. Stop Polling
   ↓
8. Disconnect All
```

---

## Code Flow

```python
import asyncio
from classes.device_manager import DeviceManager
from classes.esp32_device import DetectionEvent

# 1. Create DeviceManager (loads .env automatically)
device_manager = DeviceManager()

# 2. Set callbacks
def on_detection(event: DetectionEvent):
    print(f"{event.device_name}: {event.distance_mm}mm")

device_manager.set_detection_callback(on_detection)

async def main():
    # 3. Scan for devices (finds BM-* devices, applies whitelist)
    devices = await device_manager.scan()
    
    # 4. Connect all devices
    await device_manager.connect_all()
    
    # 5. Start polling (ESP32s enter POLLING state, ToF active)
    await device_manager.start_all()
    
    # 6. Events received via callbacks automatically
    await asyncio.sleep(30)
    
    # 7. Stop polling (ESP32s return to CONNECTED state)
    await device_manager.stop_all()
    
    # 8. Disconnect all
    await device_manager.disconnect_all()

asyncio.run(main())
```

---

## Internal Flow (What Happens Behind the Scenes)

```
DeviceManager.scan()
    │
    ├─→ BleakScanner.discover()
    │       │
    │       └─→ Finds "BM-Red", "BM-Blue", etc.
    │
    ├─→ Check DEVICE_PREFIX ("BM-")
    │
    ├─→ Check whitelist (if enabled)
    │
    └─→ _add_device()
            │
            └─→ Creates ESP32Device instance
                    │
                    └─→ Applies callbacks

DeviceManager.connect_all()
    │
    └─→ For each ESP32Device:
            │
            └─→ ESP32Device.connect()
                    │
                    ├─→ BleakClient.connect()
                    │
                    └─→ start_notify() for BLE notifications

DeviceManager.start_all()
    │
    └─→ For each ESP32Device:
            │
            └─→ ESP32Device.start_polling()
                    │
                    └─→ Sends START command (0x01) via BLE
                            │
                            └─→ ESP32 enters POLLING state
                                    │
                                    └─→ Reads ToF sensor every 25ms

ESP32 sends detection
    │
    └─→ BLE notification → ESP32Device._notification_handler()
            │
            ├─→ Parse message type (DETECTION = 0x02)
            │
            ├─→ Verify magic byte (0x42)
            │
            ├─→ Extract distance
            │
            └─→ Call on_detection(event)
                    │
                    └─→ Your callback executes
```

---

## Device States (ESP32)

```
Power On → INIT → ADVERTISING → CONNECTED → POLLING
                      ↑              ↓           ↓
                      └──────────────┴───────────┘
                         (on disconnect/stop)
```

**ADVERTISING:** Device is visible, waiting for RPI connection  
**CONNECTED:** Idle, waiting for commands  
**POLLING:** ToF sensor active, sending detections  

---
