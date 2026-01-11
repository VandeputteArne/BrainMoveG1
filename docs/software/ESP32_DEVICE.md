# ESP32Device API Reference

The `ESP32Device` class controls individual ESP32 BrainMove devices via Bluetooth Low Energy.

## Import

```python
from esp32_device import ESP32Device, DetectionEvent, BatteryEvent, StatusEvent_
```

## Creating a Device

```python
device = ESP32Device(address="AA:BB:CC:DD:EE:FF", name="BM-Blue", auto_reconnect=True)

# Parameters:
# - address: MAC address of the BLE device
# - name: Device name (e.g., "BM-Blue")
# - auto_reconnect: Enable automatic reconnection (default: True)
```

## Properties

```python
# Access device information
print(device.name)           # "BM-Blue"
print(device.address)        # "AA:BB:CC:DD:EE:FF"

# Check connection state
if device.connected:
    print("Device is connected")

if device.authenticated:
    print("Device authenticated via magic byte")

if device.is_polling:
    print("Sensors are actively polling")
```

## Connection Methods

### `connect(timeout=30.0)`

Connect to the device.

```python
success = await device.connect(timeout=30.0)
# Returns: bool (True if connected successfully)

if success:
    print("Connected!")
```

### `disconnect()`

Disconnect from the device.

```python
await device.disconnect()
# Returns: None
# Note: Disables auto-reconnect
```

## Sensor Control

### `start_polling()`

Start TOF sensor polling on the device.

```python
success = await device.start_polling()
# Returns: bool (True if command sent successfully)
```

### `stop_polling()`

Stop TOF sensor polling.

```python
success = await device.stop_polling()
# Returns: bool (True if command sent successfully)
```

## Device Commands

### `ping()`

Send a ping to the device. Device responds with PONG status event.

```python
await device.ping()
# Returns: bool (True if sent)
```

### `play_correct_sound()`

Play the "correct" sound on device buzzer.

```python
await device.play_correct_sound()
# Returns: bool (True if sent)
```

### `play_incorrect_sound()`

Play the "incorrect" sound on device buzzer.

```python
await device.play_incorrect_sound()
# Returns: bool (True if sent)
```

### `sleep()`

Put device into deep sleep mode. Wake via button press.

```python
await device.sleep()
# Returns: bool (True if sent)
# Note: Device stops polling when entering sleep
```

## Event Callbacks

Set callbacks to receive data from the device.

### Detection Events

Triggered when TOF sensor detects movement.

```python
def on_detection(event: DetectionEvent):
    print(f"Device: {event.device_name}")
    print(f"Distance: {event.distance_mm}mm")
    print(f"Device ID: {event.device_id}")
    print(f"Timestamp: {event.timestamp_ms}ms")
    print(f"Received: {event.received_at}")

device.on_detection = on_detection
```

### Battery Events

Battery status updates.

```python
def on_battery(event: BatteryEvent):
    print(f"{event.device_name} battery: {event.percent}%")
    if event.percent < 20:
        print("⚠️ Low battery!")

device.on_battery = on_battery
```

### Status Events

Device status changes (CONNECTED, PONG, SLEEPING, RECONNECTED).

```python
def on_status(event: StatusEvent_):
    print(f"Status: {event.event}")
    # event.event can be: "CONNECTED", "RECONNECTED", "SLEEPING", "PONG"

device.on_status = on_status
```



### Disconnection Events

Called when device disconnects unexpectedly.

```python
def on_disconnect():
    print("Device disconnected!")
    # Handle reconnection or error

device.on_disconnect = on_disconnect
```

## Event Data Classes

### `DetectionEvent`

```python
@dataclass
class DetectionEvent:
    device_name: str          # "BM-Blue"
    device_id: int           # 0, 1, 2, 3
    distance_mm: int         # Distance in millimeters
    timestamp_ms: int        # Device timestamp
    received_at: datetime    # When event was received
```

### `BatteryEvent`

```python
@dataclass
class BatteryEvent:
    device_name: str
    device_id: int
    percent: int             # Battery level 0-100
    timestamp_ms: int
    received_at: datetime
```

### `StatusEvent_`

```python
@dataclass
class StatusEvent_:
    device_name: str
    device_id: int
    event: str              # "CONNECTED" | "PONG" | "SLEEPING" | "RECONNECTED"
    timestamp_ms: int
    received_at: datetime
```


## Complete Example

```python
import asyncio
from esp32_device import ESP32Device

async def main():
    # Create device
    device = ESP32Device(
        address="AA:BB:CC:DD:EE:FF",
        name="BM-Blue",
        auto_reconnect=True
    )
    
    # Setup callbacks
    def on_detection(event):
        print(f"🎯 Detection: {event.distance_mm}mm")
    
    def on_battery(event):
        print(f"🔋 Battery: {event.percent}%")
    
    device.on_detection = on_detection
    device.on_battery = on_battery
    
    # Connect
    if await device.connect():
        print("✓ Connected")
        
        # Start polling
        await device.start_polling()
        
        # Run for 30 seconds
        await asyncio.sleep(30)
        
        # Cleanup
        await device.stop_polling()
        await device.disconnect()
    else:
        print("✗ Connection failed")

if __name__ == "__main__":
    asyncio.run(main())
```

## Auto-Reconnect

Devices automatically reconnect on unexpected disconnection.

```python
# Enable auto-reconnect (default)
device = ESP32Device(address="...", name="...", auto_reconnect=True)

# Disable auto-reconnect
device.auto_reconnect = False

# Manual disconnect (also disables auto-reconnect)
await device.disconnect()
```

Reconnection settings:
- Max attempts: 3
- Delay between attempts: 2 seconds
- Resumes polling if it was active before disconnect

## Constants

```python
# BLE UUIDs
SERVICE_UUID = "beb5483e-36e1-4688-b7f5-ea07361b26a7"
CHAR_DATA_UUID = "beb5483e-36e1-4688-b7f5-ea07361b26a8"
CHAR_COMMAND_UUID = "beb5483e-36e1-4688-b7f5-ea07361b26a9"

# Magic byte for authentication
MAGIC_BYTE = 0x42

# Commands (Command enum)
Command.START           # Start polling
Command.STOP            # Stop polling
Command.SLEEP           # Enter deep sleep
Command.PING            # Ping device
Command.SOUND_CORRECT   # Play correct sound
Command.SOUND_INCORRECT # Play incorrect sound

# Message types (MessageType enum)
MessageType.STATUS      # Status message
MessageType.DETECTION   # Detection event
MessageType.BATTERY     # Battery update
MessageType.KEEPALIVE   # Keepalive (silent)
```

## Error Handling

```python
try:
    success = await device.connect(timeout=30.0)
    if not success:
        print("Failed to connect - check device is powered on and in range")
except BleakError as e:
    if "not paired" in str(e).lower():
        print("Device needs pairing - use bluetoothctl")
    else:
        print(f"BLE error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Device Names & IDs

- `BM-Blue` (ID: 0)
- `BM-Red` (ID: 1)
- `BM-Yellow` (ID: 2)
- `BM-Green` (ID: 3)
