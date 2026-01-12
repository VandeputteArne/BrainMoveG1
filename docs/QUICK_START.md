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

## Callbacks Explained

### What Are Callbacks?

A **callback** is a function you provide that gets automatically executed when a specific event occurs. Think of it as "call me back when something happens."

In this system, callbacks let you respond to events from the ESP32 devices without constantly checking for them.

### Why Use Callbacks?

**Without callbacks (polling pattern):**
```python
# Bad: Have to constantly check for new data
while True:
    data = device.get_new_detection()  # Check manually
    if data:
        print(data)
    await asyncio.sleep(0.1)  # Waste CPU time checking
```

**With callbacks (event-driven):**
```python
# Good: Automatically notified when data arrives
def on_detection(event):
    print(event)  # Runs automatically when ESP32 sends data

device_manager.set_detection_callback(on_detection)
# Now you can do other work, callback fires when needed
```

### How Callbacks Work in This System

```
ESP32 sends BLE message
        ↓
ESP32Device receives notification
        ↓
_notification_handler() parses message
        ↓
Determines message type (DETECTION, BATTERY, STATUS)
        ↓
Calls appropriate handler
        ↓
Handler creates Event dataclass
        ↓
Invokes your callback with the Event
        ↓
Your function executes with the data
```

### The Three Callback Types

#### 1. Detection Callback
**Triggered when:** ESP32 detects an object (distance changes >300mm within range)

**Event Data:**
```python
@dataclass
class DetectionEvent:
    device_name: str        # "BM-Red", "BM-Blue", etc.
    device_id: int          # 0-3 (hardware device number)
    distance_mm: int        # Distance in millimeters
    timestamp_ms: int       # ESP32 timestamp (millis since boot)
    received_at: datetime   # When RPI received it (Python datetime)
```

**Example:**
```python
def on_detection(event: DetectionEvent):
    print(f"Device: {event.device_name}")
    print(f"Distance: {event.distance_mm}mm")
    print(f"Time: {event.received_at}")
    
    # Do something based on detection
    if event.distance_mm < 200:
        print("Object very close!")

device_manager.set_detection_callback(on_detection)
```

**When it fires:**
- ESP32 is in POLLING state
- ToF sensor reads distance every 25ms
- Distance is between 50mm and 1400mm
- Distance changed by more than 300mm from last sent value

#### 2. Battery Callback
**Triggered when:** ESP32 reports battery level (every 5 minutes + on connect)

**Event Data:**
```python
@dataclass
class BatteryEvent:
    device_name: str        # "BM-Red", "BM-Blue", etc.
    device_id: int          # 0-3
    percent: int            # Battery level 0-100
    timestamp_ms: int       # ESP32 timestamp
    received_at: datetime   # RPI timestamp
```

**Example:**
```python
def on_battery(event: BatteryEvent):
    print(f"{event.device_name} battery: {event.percent}%")
    
    # Alert on low battery
    if event.percent < 20:
        print(f"⚠️ WARNING: {event.device_name} low battery!")
        # Could trigger notification, email, etc.
    
    # Log battery levels
    log_battery(event.device_name, event.percent, event.received_at)

device_manager.set_battery_callback(on_battery)
```

**When it fires:**
- On connection to RPI (immediate report)
- Every 5 minutes while connected
- Regardless of CONNECTED or POLLING state

#### 3. Status Callback
**Triggered when:** ESP32 sends status updates (connect, sleep, pong)

**Event Data:**
```python
@dataclass
class StatusEvent_:
    device_name: str        # "BM-Red", "BM-Blue", etc.
    device_id: int          # 0-3
    event: str              # "CONNECTED", "SLEEPING", "PONG", etc.
    timestamp_ms: int       # ESP32 timestamp
    received_at: datetime   # RPI timestamp
```

**Example:**
```python
def on_status(event: StatusEvent_):
    print(f"{event.device_name} status: {event.event}")
    
    if event.event == "SLEEPING":
        print(f"{event.device_name} is going to sleep")
        # Update UI, log event, etc.
    
    elif event.event == "PONG":
        print(f"{event.device_name} is alive (responded to ping)")
        # Could measure latency, update health status
    
    elif event.event == "CONNECTED":
        print(f"{event.device_name} just connected!")
        # Initialize device, start polling, etc.

device_manager.set_status_callback(on_status)
```

**When it fires:**
- ESP32 connects/reconnects
- ESP32 receives SLEEP command and is about to sleep
- ESP32 receives PING command and responds with PONG

### Setting Callbacks

#### Option 1: Set on DeviceManager (applies to all devices)
```python
device_manager = DeviceManager()

# Set before or after scanning - works for all devices
device_manager.set_detection_callback(on_detection)
device_manager.set_battery_callback(on_battery)
device_manager.set_status_callback(on_status)

# Even newly discovered devices will get these callbacks
await device_manager.scan()  # Callbacks auto-applied
```

#### Option 2: Set on Individual Device
```python
# Get specific device
red_cone = device_manager.get_device("BM-Red")

# Set callbacks just for this device
red_cone.on_detection = on_detection
red_cone.on_battery = on_battery
red_cone.on_status = on_status
```

### Callback Execution Context

**Important:** Callbacks run in the asyncio event loop, so:

✅ **Safe to do:**
```python
def on_detection(event):
    print(event)                          # OK
    data.append(event)                    # OK
    asyncio.create_task(send_alert())     # OK - schedule async work
```

❌ **Don't do:**
```python
def on_detection(event):
    await some_async_function()           # ERROR - callback is not async
    time.sleep(10)                         # BAD - blocks event loop
    while True: pass                       # BAD - infinite loop freezes everything
```

**For async work in callbacks:**
```python
def on_detection(event):
    # Schedule async work without blocking
    asyncio.create_task(process_detection(event))

async def process_detection(event):
    # Now you can use await
    await save_to_database(event)
    await send_notification(event)
```

### Multiple Callbacks Example

```python
detections = []
low_battery_alerts = []

def on_detection(event: DetectionEvent):
    # Log all detections
    detections.append({
        'device': event.device_name,
        'distance': event.distance_mm,
        'time': event.received_at
    })
    print(f"Total detections: {len(detections)}")

def on_battery(event: BatteryEvent):
    # Track low battery
    if event.percent < 20:
        low_battery_alerts.append(event.device_name)
        print(f"Low battery devices: {low_battery_alerts}")

def on_status(event: StatusEvent_):
    # Log important events
    if event.event == "SLEEPING":
        print(f"Device offline: {event.device_name}")

# Apply all callbacks
device_manager.set_detection_callback(on_detection)
device_manager.set_battery_callback(on_battery)
device_manager.set_status_callback(on_status)
```

### Device-Specific Callbacks

```python
# Track different zones separately
red_zone_data = []
blue_zone_data = []

def red_detection(event: DetectionEvent):
    red_zone_data.append(event.distance_mm)
    print(f"Red zone: {len(red_zone_data)} detections")

def blue_detection(event: DetectionEvent):
    blue_zone_data.append(event.distance_mm)
    print(f"Blue zone: {len(blue_zone_data)} detections")

# Scan and set device-specific callbacks
await device_manager.scan()
await device_manager.connect_all()

red_cone = device_manager.get_device("BM-Red")
blue_cone = device_manager.get_device("BM-Blue")

red_cone.on_detection = red_detection
blue_cone.on_detection = blue_detection

await device_manager.start_all()
```

### Callback Flow Diagram

```
User Code:
    device_manager.set_detection_callback(my_function)
    await device_manager.scan()
            ↓
    DeviceManager._add_device():
            device.on_detection = my_function  ← Applied automatically
            ↓
    await device_manager.start_all()
            ↓
ESP32:
    Object detected! Send BLE message → [0x02][device_id][0x42][...distance...]
            ↓
ESP32Device:
    _notification_handler() receives bytes
            ↓
    Parse: msg_type = 0x02 (DETECTION)
            ↓
    _handle_detection_message()
            ↓
    Create: event = DetectionEvent(name="BM-Red", distance=650, ...)
            ↓
    Check: if self.on_detection is set
            ↓
    Call: self.on_detection(event)  ← Invokes your callback
            ↓
Your Code:
    my_function(event) executes
            ↓
    print(f"Detected: {event.distance_mm}mm")
```

### Summary

**Callbacks let you:**
- React to events without polling
- Keep your code clean and event-driven
- Handle multiple devices simultaneously
- Process data as it arrives in real-time

**Three callback types:**
1. **Detection** - object detected (most frequent)
2. **Battery** - battery level updates (every 5 min)
3. **Status** - connection/sleep events (occasional)

**Set once, works forever:**
```python
device_manager.set_detection_callback(on_detection)
await device_manager.scan()  # All devices auto-configured
```

---

## Key Objects

### DeviceManager
- Manages multiple ESP32Device instances
- Loads config from `.env`
- Handles scanning, connecting, health monitoring

### ESP32Device
- Represents one physical ESP32 cone
- Handles BLE communication
- Manages connection state
- Dispatches events via callbacks

---

## Quick Command Reference

```python
# DeviceManager
await device_manager.scan()                  # Find devices
await device_manager.connect_all()           # Connect all
await device_manager.start_all()             # Start polling
await device_manager.stop_all()              # Stop polling
await device_manager.disconnect_all()        # Disconnect

device_manager.get_device("BM-Red")          # Get specific device
device_manager.get_alive_devices()           # List healthy devices
device_manager.log_health_status()           # Print health summary

# Individual ESP32Device
device = device_manager.get_device("BM-Red")
await device.connect()                       # Connect
await device.start_polling()                 # Start
await device.stop_polling()                  # Stop
await device.ping()                          # Test connection
await device.play_correct_sound()            # Audio feedback
await device.disconnect()                    # Disconnect

device.connected                             # True/False
device.is_polling                            # True/False
device.is_alive()                            # True/False
```

---

## Configuration (.env)

```bash
# Required: Device MAC addresses
DEVICE_BM_BLUE=AA:BB:CC:DD:EE:01
DEVICE_BM_RED=AA:BB:CC:DD:EE:02
DEVICE_BM_YELLOW=AA:BB:CC:DD:EE:03
DEVICE_BM_GREEN=AA:BB:CC:DD:EE:04

# Optional: Timeouts and security
MAGIC_BYTE=0x42
SCAN_TIMEOUT=5.0
CONNECTION_TIMEOUT=10.0
STRICT_WHITELIST=true
```

DeviceManager loads this automatically when instantiated.

---

## Minimal Working Example

```python
#!/usr/bin/env python3
import asyncio
import sys
sys.path.insert(0, "classes")

from classes.device_manager import DeviceManager
from classes.esp32_device import DetectionEvent

device_manager = DeviceManager()

def on_detection(event: DetectionEvent):
    print(f"{event.device_name}: {event.distance_mm}mm")

async def main():
    device_manager.set_detection_callback(on_detection)
    
    await device_manager.scan()
    await device_manager.connect_all()
    await device_manager.start_all()
    
    await asyncio.sleep(30)
    
    await device_manager.disconnect_all()

asyncio.run(main())
```

**Output:**
```
BM-Red: 650mm
BM-Blue: 420mm
BM-Red: 380mm
BM-Yellow: 520mm
...
```

---

## That's It!

For detailed documentation, see:
- [USAGE_GUIDE.md](USAGE_GUIDE.md) - Complete API reference
- [SYSTEM_FLOW.md](SYSTEM_FLOW.md) - Architecture details
