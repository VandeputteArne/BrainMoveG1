# DeviceManager API Reference

The `DeviceManager` class manages discovery and control of multiple ESP32 BrainMove devices.

## Import

```python
from device_manager import DeviceManager
from esp32_device import ESP32Device, DetectionEvent, BatteryEvent
```

## Creating a Manager

```python
# Basic manager (no whitelist)
manager = DeviceManager()

# With MAC address whitelist for security
trusted_macs = {
    "AA:BB:CC:DD:EE:FF": "BM-Blue",
    "11:22:33:44:55:66": "BM-Red",
    "22:33:44:55:66:77": "BM-Yellow",
    "33:44:55:66:77:88": "BM-Green",
}

manager = DeviceManager(
    trusted_macs=trusted_macs,
    strict_whitelist=True  # Only allow devices in trusted_macs
)
```

## Properties

```python
# Get all managed devices
all_devices = manager.devices
# Returns: Dict[str, ESP32Device] - {"BM-Blue": device, "BM-Red": device, ...}

for name, device in all_devices.items():
    print(f"{name}: {device.connected}")
```

## Device Discovery

### `scan(timeout=5.0)`

Scan for BrainMove devices.

```python
devices = await manager.scan(timeout=5.0)
# Returns: List[ESP32Device] - newly discovered devices

print(f"Found {len(devices)} new device(s)")
for device in devices:
    print(f"  - {device.name} ({device.address})")
```

**Behavior:**
- Scans for devices with name prefix "BM-"
- Filters by whitelist if `strict_whitelist=True`
- Skips devices already managed
- Creates `ESP32Device` instances automatically

## Device Access

### `get_device(name)`

Get a specific device by name.

```python
blue = manager.get_device("BM-Blue")
# Returns: ESP32Device | None

if blue:
    await blue.connect()
    await blue.start_polling()
```

### `add_device(device)`

Manually add a device to the manager.

```python
custom_device = ESP32Device(address="AA:BB:CC:DD:EE:FF", name="BM-Custom")
manager.add_device(custom_device)
# Returns: None
```

## Batch Operations

### `connect_all()`

Connect to all discovered devices.

```python
results = await manager.connect_all()
# Returns: Dict[str, bool] - {"BM-Blue": True, "BM-Red": False, ...}

for name, success in results.items():
    if success:
        print(f"✓ {name} connected")
    else:
        print(f"✗ {name} failed")
```

### `disconnect_all()`

Disconnect from all devices.

```python
await manager.disconnect_all()
# Returns: None
```

### `start_all()`

Start polling on all connected devices.

```python
results = await manager.start_all()
# Returns: Dict[str, bool] - {"BM-Blue": True, ...}

# Only sends to connected devices
```

### `stop_all()`

Stop polling on all connected devices.

```python
results = await manager.stop_all()
# Returns: Dict[str, bool]
```

## Global Callbacks

Set the same callback for all managed devices.

### `set_detection_callback(callback)`

```python
def handle_detection(event: DetectionEvent):
    print(f"{event.device_name}: {event.distance_mm}mm")

manager.set_detection_callback(handle_detection)
# Applies to all current and future devices
```

### `set_battery_callback(callback)`

```python
def handle_battery(event: BatteryEvent):
    if event.percent < 20:
        print(f"⚠️ {event.device_name}: {event.percent}%")

manager.set_battery_callback(handle_battery)
```

### `set_status_callback(callback)`

```python
def handle_status(event: StatusEvent_):
    print(f"{event.device_name}: {event.event}")

manager.set_status_callback(handle_status)
```

## Complete Example

```python
import asyncio
from device_manager import DeviceManager

async def main():
    # Create manager with whitelist
    trusted_macs = {
        "AA:BB:CC:DD:EE:FF": "BM-Blue",
        "11:22:33:44:55:66": "BM-Red",
    }
    
    manager = DeviceManager(
        trusted_macs=trusted_macs,
        strict_whitelist=True
    )
    
    # Setup global callbacks
    def on_detection(event):
        print(f"🎯 {event.device_name}: {event.distance_mm}mm")
    
    def on_battery(event):
        print(f"🔋 {event.device_name}: {event.percent}%")
    
    manager.set_detection_callback(on_detection)
    manager.set_battery_callback(on_battery)
    
    # Scan for devices
    print("Scanning...")
    devices = await manager.scan(timeout=5.0)
    print(f"Found: {[d.name for d in devices]}")
    
    # Connect to all
    print("Connecting...")
    results = await manager.connect_all()
    connected = [name for name, success in results.items() if success]
    print(f"Connected to: {connected}")
    
    # Start polling
    await manager.start_all()
    print("Polling started on all devices")
    
    # Monitor for 60 seconds
    await asyncio.sleep(60)
    
    # Cleanup
    await manager.stop_all()
    await manager.disconnect_all()
    print("Shutdown complete")

if __name__ == "__main__":
    asyncio.run(main())
```

## Working with Individual Devices

You can access and control individual devices through the manager.

```python
# Scan and connect
await manager.scan()
await manager.connect_all()

# Get specific device
blue = manager.get_device("BM-Blue")
red = manager.get_device("BM-Red")

if blue:
    # Control individual device
    await blue.play_correct_sound()
    await asyncio.sleep(1)
    
    # Individual callback
    def blue_only_detection(event):
        print(f"Blue detected: {event.distance_mm}mm")
    
    blue.on_detection = blue_only_detection

if red:
    await red.play_incorrect_sound()
```

## Security: MAC Whitelisting

Use whitelist to only allow trusted devices.

```python
# Define trusted devices
TRUSTED_DEVICES = {
    "AA:BB:CC:DD:EE:FF": "BM-Blue",
    "11:22:33:44:55:66": "BM-Red",
    "22:33:44:55:66:77": "BM-Yellow",
    "33:44:55:66:77:88": "BM-Green",
}

# Enable strict whitelist
manager = DeviceManager(
    trusted_macs=TRUSTED_DEVICES,
    strict_whitelist=True
)

# During scan:
# ✓ Devices in whitelist → accepted
# ✗ Devices not in whitelist → rejected (logged as warning)
# ✗ MAC mismatch with expected name → rejected (logged as security warning)
```

**Security checks:**
1. MAC address must be in `trusted_macs`
2. Advertised name must match expected name for that MAC
3. Unknown devices are logged and rejected

## Typical Workflow

```python
# 1. Create manager
manager = DeviceManager()

# 2. Setup callbacks (before connecting)
manager.set_detection_callback(on_detection)
manager.set_battery_callback(on_battery)

# 3. Discover devices
await manager.scan()

# 4. Connect to all
await manager.connect_all()

# 5. Start monitoring
await manager.start_all()

# 6. Run application
await asyncio.Event().wait()  # Run forever

# 7. Cleanup (on shutdown)
await manager.stop_all()
await manager.disconnect_all()
```

## Error Handling

```python
try:
    devices = await manager.scan(timeout=5.0)
    if not devices:
        print("No devices found - check they are powered on")
    
    results = await manager.connect_all()
    failed = [name for name, success in results.items() if not success]
    if failed:
        print(f"Failed to connect to: {failed}")
        
except Exception as e:
    print(f"Error: {e}")
    await manager.disconnect_all()
```

## Advanced: Partial Operations

```python
# Connect only to specific devices
await manager.scan()

blue = manager.get_device("BM-Blue")
red = manager.get_device("BM-Red")

if blue:
    await blue.connect()
    await blue.start_polling()

if red:
    await red.connect()
    await red.start_polling()

# Leave other devices disconnected
```

## Combining with Individual Device Control

```python
# Use manager for discovery, then individual control
manager = DeviceManager()
await manager.scan()

# Get all devices
all_devices = manager.devices

# Control each differently
for name, device in all_devices.items():
    await device.connect()
    
    if name == "BM-Blue":
        # Blue-specific behavior
        device.on_detection = blue_handler
    elif name == "BM-Red":
        # Red-specific behavior
        device.on_detection = red_handler
    
    await device.start_polling()
```
